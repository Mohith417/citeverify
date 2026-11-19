from datetime import datetime

from pydantic import BaseModel, Field

from .claim_schema import ORM
from .enums import Confidence, ReviewedStatus, Verdict


class AIEvidencePassage(BaseModel):
    quote: str  # must be verbatim from retrieved source text (verified in code)
    source_page_or_section: str | None = None


class AIVerdictOutput(BaseModel):
    # exact JSON the AI verifier must return (Module 7)
    claim_id: str
    verdict: Verdict
    explanation: str = Field(min_length=1)
    evidence_passages: list[AIEvidencePassage] = []
    source_title: str | None = None
    source_doi: str | None = None
    source_url: str | None = None
    source_page_or_section: str | None = None
    key_supporting_facts: list[str] = []
    limitations: list[str] = []
    confidence_level: Confidence
    confidence_reason: str
    needs_human_review: bool


class ReviewEventOut(ORM):
    id: str
    action: str
    previous_verdict: str | None = None
    new_verdict: str | None = None
    note: str | None = None
    created_at: datetime


class VerificationOut(ORM):
    id: str
    verdict: Verdict
    explanation: str
    key_supporting_facts: list[str] = []
    limitations: list[str] = []
    confidence_level: Confidence
    confidence_reason: str
    evidence_basis: str
    needs_human_review: bool
    review_reasons: list[str] = []
    reviewed_status: ReviewedStatus
    reviewer_note: str | None = None
    created_at: datetime
    history: list[ReviewEventOut] = []


class ReviewUpdate(BaseModel):
    # body of POST /api/claims/{id}/review
    action: str = Field(pattern="^(confirmed|overridden|note)$")
    new_verdict: Verdict | None = None
    note: str | None = None
