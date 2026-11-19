from pydantic import BaseModel, ConfigDict, Field

from .enums import FulltextAvailability, MatchingStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExtractedClaim(BaseModel):
    # what the AI claim extractor must return (validated before saving)
    claim_text: str = Field(min_length=10)
    page_number: int | None = None
    section: str | None = None
    citation_markers: list[str] = []
    claim_category: str = "factual"


class ClaimExtractionOutput(BaseModel):
    claims: list[ExtractedClaim]


class ReferenceOut(ORM):
    id: str
    ref_label: str
    reference_text: str
    title: str | None = None
    authors: list[str] = []
    year: int | None = None
    doi: str | None = None
    journal: str | None = None
    matching_status: MatchingStatus
    matching_confidence: float | None = None
    matched_title: str | None = None
    matched_authors: list[str] = []
    matched_year: int | None = None
    matched_doi: str | None = None
    matched_source_url: str | None = None
    publication_source: str | None = None
    abstract: str | None = None
    fulltext_availability: FulltextAvailability
    fulltext_url: str | None = None
    candidates: list[dict] = []
    flags: list[str] = []


class EvidenceOut(ORM):
    id: str
    reference_id: str
    passage: str
    paragraph_id: str | None = None
    source_page: int | None = None
    source_section: str | None = None
    source_url: str | None = None
    relevance_score: float | None = None
    is_abstract_only: bool = False
    quote_verified: bool = False


class ClaimReferenceOut(ORM):
    marker: str
    match_status: str
    reference: ReferenceOut
