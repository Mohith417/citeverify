"""arXiv API provider.

Free, no API key required.
Rate limit: 1 request every 3 seconds, single connection at a time.
Good for CS/AI/physics/math preprints.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

import httpx
import feedparser

from ..config import settings
from .research_provider import NormalizedPaper, ResearchProvider

logger = logging.getLogger(__name__)

ARXIV_API = "https://export.arxiv.org/api/query"


class ArxivProvider(ResearchProvider):
    """arXiv API client for preprint discovery."""

    def __init__(self) -> None:
        self.email = settings.arxiv_email or "unknown@example.com"
        self._last_request = 0.0
        self._min_interval = 3.1  # arXiv: 1 request per 3 seconds

    def name(self) -> str:
        return "arxiv"

    def is_available(self) -> bool:
        return True

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def _get(self, params: dict) -> Optional[str]:
        try:
            self._rate_limit()
            params["email"] = self.email
            r = httpx.get(
                ARXIV_API,
                params=params,
                headers={"User-Agent": f"CiteVerify/1.0 (mailto:{self.email})"},
                timeout=30,
            )
            if r.status_code != 200:
                logger.warning("arXiv %s: %s", r.status_code, r.text[:200])
                return None
            return r.text
        except Exception as exc:  # pragma: no cover
            logger.warning("arXiv request failed: %s", exc)
            return None

    def search_by_doi(self, doi: str) -> Optional[NormalizedPaper]:
        """Search arXiv by DOI (arXiv may not index DOIs directly, but we try)."""
        # arXiv API doesn't support DOI search directly; search by title fragment instead
        return None

    def search_by_title(
        self,
        title: str,
        authors: Optional[list[str]] = None,
        year: Optional[int] = None,
    ) -> list[NormalizedPaper]:
        """Search arXiv by title."""
        # Build query: title:"..." AND submittedDate:[...]
        query = f'ti:"{title}"'
        if year:
            query += f" AND submittedDate:[{year}01010000 TO {year}12312359]"
        text = self._get({"search_query": query, "start": 0, "max_results": 5})
        if not text:
            return []
        return self._parse_feed(text)

    def find_open_access_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[str]:
        """arXiv papers are always open access. Return PDF URL."""
        if title:
            results = self.search_by_title(title)
            for p in results:
                if p.pdf_url:
                    return p.pdf_url
        return None

    def _parse_feed(self, xml_text: str) -> list[NormalizedPaper]:
        """Parse arXiv Atom feed into NormalizedPaper list."""
        try:
            feed = feedparser.parse(xml_text)
        except Exception as exc:  # pragma: no cover
            logger.warning("arXiv feed parse failed: %s", exc)
            return []
        results: list[NormalizedPaper] = []
        for entry in feed.entries:
            # Extract arXiv ID from entry id (e.g. http://arxiv.org/abs/2301.12345)
            arxiv_id = ""
            entry_id = entry.get("id", "")
            m = re.search(r"arxiv\.org/abs/(\d+\.\d+)", entry_id)
            if m:
                arxiv_id = m.group(1)
            # Extract DOI from arxiv DOI link if present
            doi = None
            for link in entry.get("links", []):
                if "doi.org" in link.get("href", ""):
                    doi = link["href"].split("doi.org/")[-1]
            # PDF URL
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else None
            # Published date
            year = None
            pub = entry.get("published") or entry.get("updated")
            if pub:
                m = re.match(r"(\d{4})", pub)
                if m:
                    year = int(m.group(1))
            authors = [a.get("name", "") for a in entry.get("authors", [])]
            results.append(
                NormalizedPaper(
                    title=entry.get("title", "").strip().replace("\n", " "),
                    authors=authors,
                    year=year,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    url=entry_id,
                    pdf_url=pdf_url,
                    abstract=entry.get("summary", "").strip(),
                    is_oa=True,
                    is_preprint=True,
                    source="arxiv",
                    source_url=entry_id,
                    confidence=0.8,
                    fulltext_url=pdf_url,
                )
            )
        return results