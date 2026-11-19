"""Module 4: original paper discovery for each parsed reference."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ..models import Document, Reference
from .arxiv_provider import ArxivProvider
from .paper_search import discover
from .research_discovery import research_discovery

logger = logging.getLogger(__name__)

DISCOVERY_FLAGS = {
    "doi_not_found", "doi_mismatch", "title_mismatch", "author_mismatch",
    "year_mismatch", "title_not_cross_checked",
}

# Large papers (60-100 pages) cite 40+ references. Look the network calls up
# concurrently but keep the count modest so public APIs are not hammered.
LOOKUP_WORKERS = 3
ARXIV_ENRICH_LIMIT = 25


def _normalise_pdf_url(url: str | None) -> str | None:
    if not url:
        return None
    if "arxiv.org/abs/" in url:
        return url.replace("/abs/", "/pdf/")
    return url


def _arxiv_pdf(
    title: str | None, year: int | None = None, authors: list[str] | None = None
) -> str | None:
    """Find an open-access arXiv PDF for an already verified title.

    Crossref/OpenAlex matches frequently carry no PDF location, and arXiv is the
    most reliable legal full text for CS/ML references. Title similarity is
    enforced *and* the publication year must agree, so a same-titled preprint of
    a different paper is never attached (e.g. the 1997 LSTM paper vs a 2021
    paper that reuses its title).
    """
    if not title or len(title) < 12:
        return None
    try:
        papers = ArxivProvider().search_by_title(title)
    except Exception as exc:  # pragma: no cover - network guard
        logger.info("arXiv full-text lookup failed for %r: %s", title, exc)
        return None
    best: tuple[float, str] | None = None
    for paper in papers:
        if not paper.pdf_url or not paper.title:
            continue
        if year and paper.year and abs(int(paper.year) - int(year)) > 2:
            continue
        score = fuzz.token_sort_ratio(title.lower(), paper.title.lower()) / 100
        if score >= 0.9 and (best is None or score > best[0]):
            best = (score, paper.pdf_url)
    return _normalise_pdf_url(best[1]) if best else None


def _lookup(ref_data: dict) -> tuple[dict, object | None]:
    """Network-only work for one reference (safe to run in a worker thread)."""
    result = discover(ref_data)
    enhanced = None
    if result["status"] != "matched":
        enhanced = research_discovery.find_paper(
            title=ref_data.get("title"),
            authors=ref_data.get("authors"),
            year=ref_data.get("year"),
            doi=ref_data.get("doi"),
        )
    return result, enhanced


def _apply(reference: Reference, result: dict, source: str) -> None:
    reference.matching_status = result["status"]
    reference.matching_confidence = result["confidence"]
    reference.candidates = result.get("candidates") or []
    flags = [f for f in (reference.flags or []) if f not in DISCOVERY_FLAGS]
    reference.flags = flags + [f for f in result.get("flags", []) if f not in flags]


def run_paper_discovery(db: Session, doc: Document, limit: int = 40,
                        only_ids: set[str] | None = None) -> dict:
    refs = [r for r in doc.references if only_ids is None or r.id in only_ids]
    refs = refs[:limit]
    counts = {"matched": 0, "ambiguous": 0, "not_found": 0, "skipped": 0, "enhanced": 0}

    lookupable = [r for r in refs if r.title or r.doi]
    payloads = {
        r.id: {"title": r.title, "authors": r.authors, "year": r.year, "doi": r.doi}
        for r in lookupable
    }
    answers: dict[str, tuple[dict, object | None]] = {}
    if payloads:
        with ThreadPoolExecutor(max_workers=LOOKUP_WORKERS) as pool:
            futures = {ref_id: pool.submit(_lookup, data) for ref_id, data in payloads.items()}
            for ref_id, future in futures.items():
                try:
                    answers[ref_id] = future.result()
                except Exception as exc:  # pragma: no cover - network guard
                    logger.info("Discovery failed for %s: %s", ref_id, exc)
                    answers[ref_id] = (
                        {"status": "not_found", "confidence": 0.0, "best": None,
                         "ranked": [], "flags": []},
                        None,
                    )

    arxiv_budget = ARXIV_ENRICH_LIMIT
    for ref in refs:
        if not (ref.title or ref.doi):
            counts["skipped"] += 1  # incomplete entry: nothing reliable to search with
            continue

        result, enhanced = answers.get(
            ref.id, ({"status": "not_found", "confidence": 0.0, "best": None,
                      "ranked": [], "flags": []}, None)
        )
        _apply(ref, result, "crossref_openalex_europepmc")
        best = result.get("best")

        if result["status"] != "matched" and enhanced and getattr(enhanced, "title", None):
            best = {
                "title": enhanced.title,
                "authors": enhanced.authors,
                "year": enhanced.year,
                "doi": enhanced.doi,
                "url": enhanced.source_url or enhanced.url,
                "journal": enhanced.journal,
                "abstract": enhanced.abstract,
                "openalex_id": enhanced.openalex_id,
                "pdf_url": enhanced.pdf_url or enhanced.fulltext_url,
                "xml_url": enhanced.xml_url,
                "is_oa": enhanced.is_oa,
                "sources": [enhanced.source],
            }
            ref.matching_status = "matched"
            ref.matching_confidence = enhanced.confidence or 0.9
            ref.flags = list(dict.fromkeys((ref.flags or []) + ["matched_via_" + enhanced.source]))
            counts["enhanced"] += 1

        if ref.matching_status == "matched" and best:
            ref.matched_title = best.get("title")
            ref.matched_authors = best.get("authors") or []
            ref.matched_year = best.get("year")
            ref.matched_doi = best.get("doi")
            ref.matched_source_url = (
                f"https://doi.org/{best['doi']}" if best.get("doi") else best.get("url")
            )
            ref.openalex_id = best.get("openalex_id")
            ref.publication_source = best.get("journal")
            ref.abstract = best.get("abstract") or ref.abstract
            ref.fulltext_url = _normalise_pdf_url(best.get("pdf_url") or best.get("xml_url"))
            if not ref.fulltext_url and arxiv_budget > 0:
                arxiv_budget -= 1
                arxiv_pdf = _arxiv_pdf(
                    ref.matched_title or ref.title, ref.matched_year or ref.year, ref.authors
                )
                if arxiv_pdf:
                    ref.fulltext_url = arxiv_pdf
                    ref.flags = list(dict.fromkeys((ref.flags or []) + ["oapdf_via_arxiv"]))
            # Full text is only confirmed by the retrieval stage.
            ref.fulltext_availability = "abstract_only" if ref.abstract else "none"
        else:
            ref.matched_title = ref.matched_doi = ref.matched_source_url = None
            ref.openalex_id = ref.publication_source = None
            ref.matched_authors, ref.matched_year = [], None
            ref.fulltext_availability = "none"

        counts[ref.matching_status if ref.matching_status in counts else "not_found"] += 1
        db.add(ref)
        db.commit()

    return {"total_references": len(doc.references), "considered": len(refs), **counts}
