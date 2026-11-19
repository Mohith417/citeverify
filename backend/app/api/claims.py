from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Claim, Verification, Reference
from ..schemas.claim_schema import ClaimReferenceOut
from ..schemas.document_schema import ClaimDetail
from ..schemas.verification_schema import VerificationOut, ReviewUpdate
from ..services import detect_issues

router = APIRouter(prefix="/api/claims", tags=["claims"])


def _get_claim(db: Session, claim_id: str) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")
    return claim


@router.get("/{claim_id}", response_model=ClaimDetail)
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    claim = _get_claim(db, claim_id)

    refs_out: list[ClaimReferenceOut] = []
    for link in claim.reference_links:
        ref = link.reference
        refs_out.append(
            ClaimReferenceOut(
                marker=link.marker,
                match_status=link.match_status,
                reference=ref,
            )
        )

    evidence_out = [
        {
            "id": e.id,
            "reference_id": e.reference_id,
            "passage": e.passage,
            "paragraph_id": e.paragraph_id,
            "source_page": e.source_page,
            "source_section": e.source_section,
            "source_url": e.source_url,
            "relevance_score": e.relevance_score,
            "is_abstract_only": e.is_abstract_only,
            "quote_verified": e.quote_verified,
        }
        for e in claim.evidence
    ]

    verification_out = None
    if claim.verification:
        v = claim.verification
        verification_out = VerificationOut(
            id=v.id,
            verdict=v.verdict,
            explanation=v.explanation,
            key_supporting_facts=v.key_supporting_facts or [],
            limitations=v.limitations or [],
            confidence_level=v.confidence_level,
            confidence_reason=v.confidence_reason,
            evidence_basis=v.evidence_basis,
            needs_human_review=v.needs_human_review,
            review_reasons=v.review_reasons or [],
            reviewed_status=v.reviewed_status,
            reviewer_note=v.reviewer_note,
            created_at=v.created_at,
            history=[],
        )

    return ClaimDetail(
        claim_id=claim.id,
        claim_text=claim.claim_text,
        page_number=claim.page_number,
        section=claim.section,
        citation_markers=claim.citation_markers or [],
        claim_category=claim.claim_category,
        flags=claim.flags or [],
        references=refs_out,
        evidence=evidence_out,
        verification=verification_out,
    )


@router.post("/{claim_id}/review", response_model=VerificationOut)
def review_claim(claim_id: str, update: ReviewUpdate, db: Session = Depends(get_db)):
    claim = _get_claim(db, claim_id)
    v = db.query(Verification).filter(Verification.claim_id == claim.id).first()
    if v is None:
        raise HTTPException(status_code=404, detail="No verification found for this claim.")

    previous = v.verdict
    if update.action == "overridden" and update.new_verdict:
        v.verdict = update.new_verdict
        v.reviewed_status = "overridden"
    elif update.action == "confirmed":
        v.reviewed_status = "confirmed"
    if update.note is not None:
        v.reviewer_note = update.note

    db.add(v)
    db.commit()
    db.refresh(v)

    return VerificationOut(
        id=v.id,
        verdict=v.verdict,
        explanation=v.explanation,
        key_supporting_facts=v.key_supporting_facts or [],
        limitations=v.limitations or [],
        confidence_level=v.confidence_level,
        confidence_reason=v.confidence_reason,
        evidence_basis=v.evidence_basis,
        needs_human_review=v.needs_human_review,
        review_reasons=v.review_reasons or [],
        reviewed_status=v.reviewed_status,
        reviewer_note=v.reviewer_note,
        created_at=v.created_at,
        history=[],
    )