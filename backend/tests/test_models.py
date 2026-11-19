from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.database import Base
from app.schemas.document_schema import ClaimDetail
from app.schemas.verification_schema import AIVerdictOutput


def make_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_relationships_and_schema_roundtrip():
    s = make_session()
    doc = models.Document(filename="a.pdf", stored_path="x")
    claim = models.Claim(document=doc, claim_text="Drug X reduced mortality by 20%.",
                         page_number=2, citation_markers=["[1]"])
    ref = models.Reference(document=doc, ref_label="1", reference_text="Smith 2020 ...")
    claim.reference_links.append(models.ClaimReference(reference=ref, marker="[1]"))
    claim.verification = models.Verification(verdict="partially_supported", confidence_level="medium")
    s.add(doc)
    s.commit()

    c = s.get(models.Claim, claim.id)
    detail = ClaimDetail(
        claim_id=c.id, claim_text=c.claim_text, page_number=c.page_number,
        citation_markers=c.citation_markers, claim_category=c.claim_category,
        references=[type("L", (), {"marker": l.marker, "match_status": l.match_status,
                                   "reference": l.reference})() for l in c.reference_links],
        verification=c.verification,
    )
    assert detail.verification.verdict.value == "partially_supported"
    assert detail.references[0].reference.matching_status.value == "pending"

    s.delete(doc)
    s.commit()
    assert s.query(models.Claim).count() == 0  # cascade works


def test_ai_output_validation():
    out = AIVerdictOutput.model_validate({
        "claim_id": "c1", "verdict": "supported", "explanation": "ok",
        "confidence_level": "high", "confidence_reason": "direct", "needs_human_review": False})
    assert out.verdict.value == "supported"
