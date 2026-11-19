"""Semantic Scholar API provider.

Free tier: API key recommended (request via https://api.semanticscholar.org).
Unauthenticated: 1000 req/sec shared among all users, may be throttled.
Authenticated: 1 req/sec intro rate limit.
Provides: paper metadata, abstracts, PDF URLs, citation relationships.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from ..config import settings
from .research_provider import NormalizedPaper, ResearchProvider, normalized_title

logger = logging.getLogger(__name__)

S2_BASE = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarProvider(ResearchProvider):
    """Semantic Scholar Academic Graph API client."""

    def __init__(self) -> None:
        self.api_key = settings.semantic_scholar_api_key
        self._last_request = 0.0
        self._min_interval = 1.1  # respect 1 RPS intro limit when authenticated

    def name(self) -> str:
        return "semantic_scholar"

    def is_available(self) -> bool:
        return True  # public endpoints available without key

    def _headers(self) -> dict:
        h = {"User-Agent": "CiteVerify/1.0"}
        if self.api_key:
            h["x-api-key"] = self.api_key
        return h

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _get(self, url: str, params: dict) -> Optional[dict]:
        try:
            self._rate_limit()
            r = httpx.get(url, params=params, headers=self._headers(), timeout=20)
            if r.status_code == 429:
                logger.warning("Semantic Scholar rate limited")
                return None
            if r.status_code != 200:
                logger.warning("Semantic Scholar %s: %s", r.status_code, r.text[:200])
                return None
            return r.json()
        except Exception as exc:  # pragma: no cover
            logger.warning("Semantic Scholar request failed: %s", exc)
            return None

    def search_by_doi(self, doi: str) -> Optional[NormalizedPaper]:
        """Look up a paper by DOI."""
        data = self._get(
            f"{S2_BASE}/paper/DOI:{doi}",
            params={
                "fields": "title,authors,year,externalIds,abstract,openAccessPdf,url,isOpenAccess,venue,journal,year,publicationTypes"
            },
        )
        if not data:
            return None
        return self._paper_from_s2(data)

    def search_by_title(
        self,
        title: str,
        authors: Optional[list[str]] = None,
        year: Optional[int] = None,
    ) -> list[NormalizedPaper]:
        """Search papers by title."""
        params: dict = {"query": title, "limit": 5, "fields": "title,authors,year,externalIds,abstract,openAccessPdf,url,isOpenAccess,venue,publicationTypes"}
        if year:
            params["year"] = f"{year}-{year}"
        data = self._get(f"{S2_BASE}/paper/search", params=params)
        if not data:
            return []
        results: list[NormalizedPaper] = []
        for item in data.get("data", []):
            p = self._paper_from_s2(item)
            # Boost confidence if author/year match
            if authors and p.authors:
                p.authors = p.authors  # keep
            results.append(p)
        return results

    def find_open_access_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[str]:
        """Return an open-access PDF URL if available."""
        if doi:
            p = self.search_by_doi(doi)
            if p and p.pdf_url:
                return p.pdf_url
        if title:
            results = self.search_by_title(title)
            for p in results:
                if p.pdf_url:
                    return p.pdf_url
        return None

    def _paper_from_s2(self, data: dict) -> NormalizedPaper:
        ext_ids = data.get("externalIds") or {}
        oa = data.get("openAccessPdf") or {}
        authors = []
        for a in data.get("authors") or []:
            nm = a.get("name")
            if nm:
                authors.append(nm)
        pub_types = data.get("publicationTypes") or []
        is_preprint = any("preprint" in str(t).lower() for t in pub_types)
        return NormalizedPaper(
            title=data.get("title", ""),
            authors=authors,
            year=data.get("year"),
            doi=ext_ids.get("DOI"),
            pmid=ext_ids.get("PubMed"),
            arxiv_id=ext_ids.get("ArXiv"),
            url=data.get("url"),
            pdf_url=oa.get("url") if oa else None,
            abstract=data.get("abstract"),
            journal=data.get("venue") or data.get("journal"),
            is_oa=data.get("isOpenAccess", False),
            is_preprint=is_preprint,
            source="semantic_scholar",
            source_url=data.get("url"),
            confidence=0.85,
            fulltext_url=oa.get("url") if oa else None,
        )