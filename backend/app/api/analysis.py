"""Analysis endpoints: start the verification pipeline, poll status, read results."""

from __future__ import annotations

import logging
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..models import Claim, ClaimReference, Document, Evidence, Reference, Verification
from ..schemas.claim_schema import ReferenceOut
from ..schemas.document_schema import ClaimRow, DocumentOut, DocumentResults, StatusOut, Summary
from ..services import claim_extractor, ai_verifier, detect_issues
from ..services.citation_extractor import find_citations
from ..services.citation_pipeline import match_marker, run_citation_extraction
from ..services.discovery_pipeline import run_paper_discovery
from ..services.evidence_retrieval import retrieve_relevant_passages, split_into_paragraphs
from ..services.fulltext_retriever import retrieve_full_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["analysis"])

ACTIVE_STATES = {
    "extracting", "searching_references", "retrieving_evidence",
    "comparing_claims", "generating_report",
}


def _get_doc(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


def _set_status(db: Session, doc: Document, status: str, message: str = "") -> None:
    doc.processing_status = status
    doc.stage_message = message
    db.add(doc)
    db.commit()


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).limit(25).all()
    return docs


@router.get("/{document_id}/status", response_model=StatusOut)
def get_status(document_id: str, db: Session = Depends(get_db)):
    return _get_doc(db, document_id)


@router.post("/{document_id}/extract-citations")
def extract_citations(document_id: str, db: Session = Depends(get_db)):
    """Inspect citation/reference parsing on its own (used by the tests and for debugging)."""
    doc = _get_doc(db, document_id)
    if doc.needs_ocr:
        raise HTTPException(status_code=400, detail="Scanned PDF: OCR is required before analysis.")
    return run_citation_extraction(db, doc)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def _status(db, doc, status, message):
    _set_status(db, doc, status, message)


def _run_pipeline(document_id: str) -> None:
    db = SessionLocal()
    doc = db.get(Document, document_id)
    if doc is None:
        db.close()
        return
    try:
        _status(db, doc, "extracting", "Extracting citations and scientific claims...")
        run_citation_extraction(db, doc)
        doc = db.get(Document, document_id)

        pages = [(p.page_number, p.text) for p in sorted(doc.pages, key=lambda p: p.page_number)]
        extracted = claim_extractor.extract_claims(pages)
        for claim in list(doc.claims):
            db.delete(claim)
        db.commit()
        doc = db.get(Document, document_id)

        claim_objs: list[Claim] = []
        for item in extracted:
            # The LLM occasionally drops in-text markers; recover them from the
            # verbatim claim text so citation linking never depends on that.
            markers = list(item.citation_markers or [])
            markers += [c.marker for c in find_citations(item.claim_text)]
            markers = [m for m in dict.fromkeys(markers) if m.strip()]
            claim = Claim(
                document_id=doc.id,
                claim_text=item.claim_text,
                page_number=item.page_number,
                section=item.section,
                citation_markers=markers,
                claim_category=item.claim_category,
                flags=[],
            )
            db.add(claim)
            claim_objs.append(claim)
        db.commit()
        for claim in claim_objs:
            db.refresh(claim)

        # Map every marker to a reference row.
        cited_ids: set[str] = set()
        for claim in claim_objs:
            linked: set[str] = set()
            for marker in claim.citation_markers or []:
                for ref, status in match_marker(marker, doc.references):
                    if ref.id in linked:
                        continue
                    linked.add(ref.id)
                    db.add(ClaimReference(
                        claim_id=claim.id, reference_id=ref.id, marker=marker, match_status=status,
                    ))
                    if status == "matched":
                        cited_ids.add(ref.id)
            db.commit()

        _status(db, doc, "searching_references",
                f"Matching {len(cited_ids)} cited references to original publications...")
        if doc.references:
            run_paper_discovery(db, doc, limit=settings.max_references, only_ids=cited_ids or None)
        doc = db.get(Document, document_id)

        _status(db, doc, "retrieving_evidence", "Retrieving open-access full text...")
        fulltext_cache: dict[str, dict] = {}
        # Verify the claims that actually carry a citation first; a claim with no
        # source can only ever be "insufficient evidence", so spending the
        # comparison budget on it would leave real citations unchecked.
        ordered = sorted(
            claim_objs,
            key=lambda c: 0 if (c.citation_markers and any(
                link.match_status == "matched" for link in c.reference_links
            )) else 1,
        )
        to_verify = ordered[: settings.max_verify_claims]
        total = max(1, len(to_verify))

        for index, claim in enumerate(to_verify, start=1):
            _status(db, doc, "comparing_claims",
                   f"Comparing claim {index}/{total} against its cited research...")
            links = [link for link in claim.reference_links if link.match_status == "matched"]
            ambiguous = [link for link in claim.reference_links if link.match_status == "ambiguous"]
            if not links:
                reason = (
                    "The citation marker could not be matched unambiguously to a single reference entry."
                    if ambiguous else
                    "No citation was attached to this statement, so there is no source to verify against."
                )
                db.add(Verification(
                    claim_id=claim.id, verdict="insufficient_evidence", explanation=reason,
                    key_supporting_facts=[], limitations=["No verifiable source reference"],
                    confidence_level="low", confidence_reason=reason,
                    evidence_basis="none", needs_human_review=True,
                    review_reasons=["ambiguous_citation" if ambiguous else "missing_citation"],
                    reviewed_status="pending",
                ))
                claim.flags = list(dict.fromkeys((claim.flags or []) + [
                    "ambiguous_citation" if ambiguous else "missing_citation"
                ]))
                db.add(claim)
                db.commit()
                continue

            ref = links[0].reference
            cached = fulltext_cache.get(ref.id)
            if cached is None:
                result = retrieve_full_text(
                    doi=ref.matched_doi or ref.doi,
                    title=ref.matched_title or ref.title,
                    openalex_id=ref.openalex_id,
                    pdf_url=ref.fulltext_url,
                    abstract=ref.abstract,
                    xml_url=ref.fulltext_url if ref.fulltext_url and "fullTextXML" in ref.fulltext_url else None,
                )
                cached = {
                    "text": result.full_text,
                    "availability": result.full_text_availability,
                    "source_url": result.source_url,
                    "evidence_source": result.evidence_source,
                }
                fulltext_cache[ref.id] = cached
                ref.fulltext_availability = result.full_text_availability
                if result.source_url:
                    ref.matched_source_url = result.source_url
                if result.pdf_url:
                    ref.fulltext_url = result.pdf_url
                db.add(ref)
                db.commit()

            evidence_passages: list[str] = []
            evidence_rows: list[Evidence] = []
            section = None
            if cached["text"]:
                paragraphs = split_into_paragraphs(
                    cached["text"],
                    source_title=ref.matched_title or ref.title or "",
                    source_url=ref.matched_source_url,
                    source_doi=ref.matched_doi,
                )
                for para, score in retrieve_relevant_passages(
                    claim.claim_text, paragraphs, top_k=settings.evidence_top_k
                ):
                    section = section or para.source_section
                    evidence_passages.append(para.text)
                    evidence_rows.append(Evidence(
                        claim_id=claim.id, reference_id=ref.id, passage=para.text,
                        paragraph_id=para.paragraph_id, source_section=para.source_section,
                        source_url=ref.matched_source_url, relevance_score=score,
                        is_abstract_only=False, quote_verified=True,
                    ))
            elif ref.abstract:
                evidence_passages.append(ref.abstract)
                evidence_rows.append(Evidence(
                    claim_id=claim.id, reference_id=ref.id, passage=ref.abstract,
                    paragraph_id="abstract", source_section="Abstract",
                    source_url=ref.matched_source_url, relevance_score=1.0,
                    is_abstract_only=True, quote_verified=True,
                ))
                section = "Abstract"

            for row in evidence_rows:
                db.add(row)
            db.commit()

            context_parts = [f"Title: {ref.matched_title}"] if ref.matched_title else []
            if ref.matched_authors:
                context_parts.append("Authors: " + ", ".join(ref.matched_authors[:6]))
            if ref.matched_year:
                context_parts.append(f"Year: {ref.matched_year}")
            if ref.publication_source:
                context_parts.append(f"Venue: {ref.publication_source}")

            verdict = ai_verifier.verify_claim(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                citation_markers=claim.citation_markers or [],
                source_title=ref.matched_title or ref.title,
                source_doi=ref.matched_doi or ref.doi,
                source_url=ref.matched_source_url,
                evidence_passages=evidence_passages,
                source_page_or_section=section,
                study_context="; ".join(context_parts),
                abstract_only=cached["availability"] == "abstract_only",
            )

            db.add(Verification(
                claim_id=claim.id,
                verdict=verdict.verdict,
                explanation=verdict.explanation,
                key_supporting_facts=verdict.key_supporting_facts,
                limitations=verdict.limitations,
                confidence_level=verdict.confidence_level,
                confidence_reason=verdict.confidence_reason,
                evidence_basis=cached["availability"],
                needs_human_review=verdict.needs_human_review,
                review_reasons=[],
                reviewed_status="pending",
            ))
            db.commit()
            # Free AI tiers are token-per-minute limited; smooth the request rate.
            if ai_verifier.is_available():
                time.sleep(1.0)

        # Claims beyond the configured verification limit stay explicitly unverified.
        for claim in ordered[settings.max_verify_claims:]:
            db.add(Verification(
                claim_id=claim.id, verdict="insufficient_evidence",
                explanation="This claim was extracted but not compared in this run (verification limit reached).",
                key_supporting_facts=[], limitations=["Not verified in this run"],
                confidence_level="low", confidence_reason="Verification limit reached.",
                evidence_basis="none", needs_human_review=True,
                review_reasons=["not_verified"], reviewed_status="pending",
            ))
        db.commit()

        _status(db, doc, "generating_report", "Flagging misleading references...")
        for claim in claim_objs:
            links = [link for link in claim.reference_links if link.match_status == "matched"]
            ref = links[0].reference if links else None
            verification = db.query(Verification).filter(Verification.claim_id == claim.id).first()
            flags = detect_issues(claim=claim, reference=ref, verification=verification)
            if flags:
                claim.flags = list(dict.fromkeys((claim.flags or []) + flags))
                db.add(claim)
                if verification:
                    verification.review_reasons = list(dict.fromkeys(
                        (verification.review_reasons or []) + flags
                    ))
                    if verification.verdict != "supported":
                        verification.needs_human_review = True
                    db.add(verification)
        db.commit()

        _status(db, doc, "completed", "Verification report ready.")
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Analysis pipeline failed for %s", document_id)
        try:
            doc.error = str(exc)[:2000]
            doc.processing_status = "failed"
            doc.stage_message = f"Analysis failed: {exc}"
            db.add(doc)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/{document_id}/analyze", response_model=StatusOut)
def analyze(document_id: str, db: Session = Depends(get_db)):
    doc = _get_doc(db, document_id)
    if doc.needs_ocr:
        raise HTTPException(status_code=400, detail="Scanned PDF: OCR is required before analysis.")
    if doc.processing_status in ACTIVE_STATES:
        return doc  # already running; the client can keep polling
    doc.error = None
    _set_status(db, doc, "extracting", "Starting analysis...")
    threading.Thread(target=_run_pipeline, args=(document_id,), daemon=True).start()
    return doc


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
def _build_summary(db: Session, doc: Document) -> Summary:
    claims = db.query(Claim).filter(Claim.document_id == doc.id).all()
    refs = db.query(Reference).filter(Reference.document_id == doc.id).all()
    summary = Summary()
    summary.total_claims = len(claims)
    summary.total_citations = sum(len(c.citation_markers or []) for c in claims)
    summary.references_matched = sum(1 for r in refs if r.matching_status == "matched")
    cited_ids = {
        link.reference_id
        for claim in claims
        for link in claim.reference_links
        if link.match_status == "matched" and link.reference_id
    }
    summary.references_cited = len(cited_ids)
    summary.papers_retrieved = sum(1 for r in refs if r.fulltext_availability == "full_text")
    for claim in claims:
        v = claim.verification
        if v is None:
            continue
        key = v.verdict
        if hasattr(summary, key):
            setattr(summary, key, getattr(summary, key) + 1)
        if v.needs_human_review:
            summary.needs_human_review += 1
    return summary


@router.get("/{document_id}/results", response_model=DocumentResults)
def get_results(document_id: str, db: Session = Depends(get_db)):
    doc = _get_doc(db, document_id)
    claims = (
        db.query(Claim)
        .filter(Claim.document_id == doc.id)
        .order_by(Claim.page_number.asc().nulls_last(), Claim.id)
        .all()
    )
    # Order claims by where they actually appear in the document text.
    def normalise(value: str) -> str:
        return " ".join((value or "").split()).lower()

    page_text = {p.page_number: normalise(p.text) for p in doc.pages}

    def position(claim: Claim) -> tuple[int, int]:
        text = page_text.get(claim.page_number or 0, "")
        needle = normalise(claim.claim_text)[:60]
        index = text.find(needle) if needle else -1
        return (claim.page_number or 0, index if index >= 0 else 10**6)

    claims.sort(key=position)
    rows: list[ClaimRow] = []
    for claim in claims:
        v = claim.verification
        links = [link for link in claim.reference_links if link.match_status == "matched"]
        source_title = None
        if links:
            source_title = links[0].reference.matched_title or links[0].reference.title
        rows.append(ClaimRow(
            claim_id=claim.id,
            claim_text=claim.claim_text,
            page_number=claim.page_number,
            citation_markers=claim.citation_markers or [],
            source_title=source_title,
            verdict=v.verdict if v else None,
            confidence_level=v.confidence_level if v else None,
            needs_human_review=v.needs_human_review if v else True,
            reviewed_status=v.reviewed_status if v else "pending",
            flags=claim.flags or [],
        ))

    return DocumentResults(
        document=DocumentOut.model_validate(doc),
        summary=_build_summary(db, doc),
        claims=rows,
        references=[ReferenceOut.model_validate(r) for r in doc.references],
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = _get_doc(db, document_id)
    stored = doc.stored_path
    db.delete(doc)
    db.commit()
    try:
        from pathlib import Path

        Path(stored).unlink(missing_ok=True)
    except OSError:
        pass
    return {"deleted": document_id}
