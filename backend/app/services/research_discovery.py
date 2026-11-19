"""Multi-provider research discovery orchestrator.

Providers are queried in priority order and results deduplicated by DOI, PMID,
arXiv ID and normalized title/author matching. A candidate is only accepted when
its title actually matches the cited reference (or the DOI matches exactly), so a
merely similar paper is never silently treated as the cited source.
"""

from __future__ import annotations

import logging
from typing import Optional

from rapidfuzz import fuzz

from .research_provider import NormalizedPaper, ResearchProvider, merge_papers, papers_match
from .semantic_scholar_provider import SemanticScholarProvider
from .unpaywall_provider import UnpaywallProvider
from .arxiv_provider import ArxivProvider

logger = logging.getLogger(__name__)

TITLE_ACCEPT = 0.86


class ResearchDiscovery:
    def __init__(self) -> None:
        self.providers: list[ResearchProvider] = []
        for provider in (SemanticScholarProvider(), UnpaywallProvider(), ArxivProvider()):
            try:
                if provider.is_available():
                    self.providers.append(provider)
            except Exception as exc:  # pragma: no cover
                logger.info("Provider %s unavailable: %s", provider.name(), exc)

    # ------------------------------------------------------------------
    def find_paper(
        self,
        title: Optional[str] = None,
        authors: Optional[list[str]] = None,
        year: Optional[int] = None,
        doi: Optional[str] = None,
    ) -> Optional[NormalizedPaper]:
        candidates: list[NormalizedPaper] = []

        if doi:
            for provider in self.providers:
                try:
                    paper = provider.search_by_doi(doi)
                    if paper:
                        candidates.append(paper)
                except Exception as exc:  # pragma: no cover
                    logger.info("%s DOI lookup failed: %s", provider.name(), exc)

        if title:
            for provider in self.providers:
                try:
                    candidates.extend(provider.search_by_title(title, authors=authors, year=year))
                except Exception as exc:  # pragma: no cover
                    logger.info("%s title search failed: %s", provider.name(), exc)

        if not candidates:
            return None
        best = self._select_best(candidates, doi=doi, title=title)
        return self._verified(best, doi=doi, title=title)

    def find_open_access_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[str]:
        for provider in self.providers:
            if provider.name() not in ("unpaywall", "semantic_scholar", "arxiv"):
                continue
            try:
                found = provider.find_open_access_full_text(doi=doi, title=title, url=url)
                if found:
                    return found
            except Exception as exc:  # pragma: no cover
                logger.info("%s full-text lookup failed: %s", provider.name(), exc)
        return None

    # ------------------------------------------------------------------
    def _verified(
        self,
        paper: Optional[NormalizedPaper],
        *,
        doi: Optional[str],
        title: Optional[str],
    ) -> Optional[NormalizedPaper]:
        if paper is None:
            return None
        if doi and paper.doi and paper.doi.lower() == doi.lower():
            return paper
        if title and paper.title:
            score = max(
                fuzz.ratio(title.lower(), paper.title.lower()),
                fuzz.token_sort_ratio(title.lower(), paper.title.lower()),
            ) / 100
            paper.confidence = round(score, 2)
            if score >= TITLE_ACCEPT:
                return paper
            return None
        return None

    def _select_best(
        self,
        candidates: list[NormalizedPaper],
        *,
        doi: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[NormalizedPaper]:
        by_key: dict[str, NormalizedPaper] = {}
        unmatched: list[NormalizedPaper] = []
        for p in candidates:
            if p.doi:
                key = p.doi.lower()
                by_key[key] = merge_papers(by_key[key], p) if key in by_key else p
            else:
                unmatched.append(p)
        merged = list(by_key.values())
        for p in unmatched:
            for i, existing in enumerate(merged):
                if papers_match(existing, p):
                    merged[i] = merge_papers(existing, p)
                    break
            else:
                merged.append(p)

        if doi:
            for p in merged:
                if p.doi and p.doi.lower() == doi.lower():
                    return p
        if title:
            target = " ".join(title.lower().split())
            for p in merged:
                if p.title and " ".join(p.title.lower().split()) == target:
                    return p
        if not merged:
            return None
        return max(merged, key=lambda p: p.confidence)


research_discovery = ResearchDiscovery()
