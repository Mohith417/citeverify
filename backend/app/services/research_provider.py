"""Modular research-provider interface.

Normalizes publication metadata from different APIs into a common schema.
Providers are tried in priority order. Results are deduplicated by DOI,
PMID, arXiv ID, and normalized title/author matching.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NormalizedPaper:
    """Common schema for publication metadata from any provider."""
    title: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    xml_url: Optional[str] = None
    abstract: Optional[str] = None
    journal: Optional[str] = None
    openalex_id: Optional[str] = None
    is_oa: bool = False
    is_preprint: bool = False
    source: str = ""  # provider name (e.g. "semantic_scholar", "unpaywall", "arxiv")
    source_url: Optional[str] = None  # landing page URL on provider site
    confidence: float = 0.0  # 0.0-1.0 match confidence
    fulltext_url: Optional[str] = None  # best legal OA full-text URL


class ResearchProvider(ABC):
    """Abstract base class for research paper discovery providers."""

    @abstractmethod
    def name(self) -> str:
        """Return a short provider identifier."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""

    @abstractmethod
    def search_by_doi(self, doi: str) -> Optional[NormalizedPaper]:
        """Search for a paper by DOI. Returns best match or None."""

    @abstractmethod
    def search_by_title(
        self,
        title: str,
        authors: Optional[list[str]] = None,
        year: Optional[int] = None,
    ) -> list[NormalizedPaper]:
        """Search for papers by title. Returns ranked candidates."""

    @abstractmethod
    def find_open_access_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[str]:
        """Return a legal open-access full-text URL (PDF or HTML/XML), or None."""


def normalized_title(title: str) -> str:
    """Return a lowercase, whitespace-normalized title for dedup comparison."""
    return " ".join(title.lower().split()) if title else ""


def papers_match(p1: NormalizedPaper, p2: NormalizedPaper) -> bool:
    """Determine if two NormalizedPaper records refer to the same publication."""
    # DOI match is strongest
    if p1.doi and p2.doi and p1.doi.lower() == p2.doi.lower():
        return True
    # PMID match
    if p1.pmid and p2.pmid and p1.pmid == p2.pmid:
        return True
    # arXiv ID match
    if p1.arxiv_id and p2.arxiv_id and p1.arxiv_id == p2.arxiv_id:
        return True
    # Title + first author + year match (fuzzy)
    if (
        p1.title
        and p2.title
        and normalized_title(p1.title) == normalized_title(p2.title)
        and p1.year
        and p2.year
        and p1.year == p2.year
    ):
        if p1.authors and p2.authors:
            a1 = p1.authors[0].lower().split()[-1] if p1.authors[0] else ""
            a2 = p2.authors[0].lower().split()[-1] if p2.authors[0] else ""
            if a1 and a2 and a1 == a2:
                return True
    return False


def merge_papers(primary: NormalizedPaper, secondary: NormalizedPaper) -> NormalizedPaper:
    """Merge secondary paper metadata into primary, filling missing fields."""
    merged = NormalizedPaper(
        title=primary.title or secondary.title,
        authors=primary.authors or secondary.authors,
        year=primary.year or secondary.year,
        doi=primary.doi or secondary.doi,
        pmid=primary.pmid or secondary.pmid,
        arxiv_id=primary.arxiv_id or secondary.arxiv_id,
        url=primary.url or secondary.url,
        pdf_url=primary.pdf_url or secondary.pdf_url,
        xml_url=primary.xml_url or secondary.xml_url,
        abstract=primary.abstract or secondary.abstract,
        journal=primary.journal or secondary.journal,
        openalex_id=primary.openalex_id or secondary.openalex_id,
        is_oa=primary.is_oa or secondary.is_oa,
        is_preprint=primary.is_preprint or secondary.is_preprint,
        source=primary.source,
        source_url=primary.source_url or secondary.source_url,
        confidence=max(primary.confidence, secondary.confidence),
        fulltext_url=primary.fulltext_url or secondary.fulltext_url,
    )
    return merged