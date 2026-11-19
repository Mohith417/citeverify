from datetime import datetime

from pydantic import BaseModel

from .claim_schema import ClaimReferenceOut, EvidenceOut, ORM, ReferenceOut
from .enums import Confidence, ProcessingStatus, Verdict
from .verification_schema import VerificationOut


class DocumentOut(ORM):
    id: str
    filename: str
    uploaded_at: datetime
    processing_status: ProcessingStatus
    page_count: int = 0
    needs_ocr: bool = False


class StatusOut(ORM):
    id: str
    processing_status: ProcessingStatus
    stage_message: str = ""
    error: str | None = None


class Summary(BaseModel):
    # every number is computed from DB rows, never hardcoded
    total_claims: int = 0
    total_citations: int = 0
    references_matched: int = 0
    papers_retrieved: int = 0
    supported: int = 0
    partially_supported: int = 0
    unsupported: int = 0
    contradictory: int = 0
    potentially_outdated: int = 0
    insufficient_evidence: int = 0
    needs_human_review: int = 0


class ClaimRow(BaseModel):
    claim_id: str
    claim_text: str
    page_number: int | None = None
    citation_markers: list[str] = []
    source_title: str | None = None
    verdict: Verdict | None = None
    confidence_level: Confidence | None = None
    needs_human_review: bool = True
    reviewed_status: str = "pending"
    flags: list[str] = []


class DocumentResults(BaseModel):
    document: DocumentOut
    summary: Summary
    claims: list[ClaimRow]
    references: list[ReferenceOut]


class ClaimDetail(BaseModel):
    claim_id: str
    claim_text: str
    page_number: int | None = None
    section: str | None = None
    citation_markers: list[str] = []
    claim_category: str
    flags: list[str] = []
    references: list[ClaimReferenceOut] = []
    evidence: list[EvidenceOut] = []
    verification: VerificationOut | None = None
