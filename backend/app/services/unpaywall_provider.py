"""Unpaywall API provider.

Free: requires an email address as query parameter.
Finds legal open-access copies of research papers.
Returns best OA location (PDF or landing page).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..config import settings
from .research_provider import NormalizedPaper, ResearchProvider

logger = logging.getLogger(__name__)

UNPAYWALL_BASE = "https://api.unpaywall.org/v2"


class UnpaywallProvider(ResearchProvider):
    """Unpaywall client for finding legal open-access full-text."""

    def __init__(self) -> None:
        self.email = settings.unpaywall_email or settings.contact_email

    def name(self) -> str:
        return "unpaywall"

    def is_available(self) -> bool:
        return bool(settings.unpaywall_email or settings.contact_email)

    def search_by_doi(self, doi: str) -> Optional[NormalizedPaper]:
        """Unpaywall doesn't support DOI lookup returning full metadata,
        but we can use it to find OA locations. Returns minimal paper."""
        oa_url = self.find_open_access_full_text(doi=doi)
        if oa_url:
            return NormalizedPaper(
                title="",
                doi=doi,
                url=oa_url,
                pdf_url=oa_url,
                fulltext_url=oa_url,
                source="unpaywall",
                source_url=oa_url,
                confidence=0.7,
            )
        return None

    def search_by_title(
        self,
        title: str,
        authors: Optional[list[str]] = None,
        year: Optional[int] = None,
    ) -> list[NormalizedPaper]:
        """Unpaywall requires a DOI, so title search is not supported."""
        return []

    def find_open_access_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[str]:
        """Return the best legal open-access full-text URL for a DOI."""
        if not doi:
            return None
        try:
            r = httpx.get(
                f"{UNPAYWALL_BASE}/{doi}",
                params={"email": self.email},
                headers={"User-Agent": "CiteVerify/1.0"},
                timeout=20,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            best = data.get("best_oa_location") or {}
            # Prefer PDF URL, fall back to landing page
            pdf = best.get("url_for_pdf") or best.get("url")
            if pdf:
                return pdf
            # Check other OA locations
            for loc in data.get("oa_locations") or []:
                u = loc.get("url_for_pdf") or loc.get("url")
                if u:
                    return u
        except Exception as exc:  # pragma: no cover
            logger.warning("Unpaywall request failed: %s", exc)
        return None