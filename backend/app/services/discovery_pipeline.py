"""Module 4: original paper discovery for each parsed reference."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import Document, Reference
from .paper_search import discover
from .research_discovery import research_discovery

logger = logging.getLogger(__name__)

DISCOVERY_FLAGS = {
    "doi_not_found", "doi_mismatch", "title_mismatch", "author_mismatch",
    "year_mismatch", "title_not_cross_checked",
}


def _apply(reference: Reference, result: dict, source: str) -> None:
    reference.matching_status = result["status"]
    reference.matching_confidence = result["confidence"]
    reference.candidates = result.get("candidates") or []
    flags = [f for f in (reference.flags or []) if f not in DISCOVERY_FLAGS]
    reference.flags = flags + [f for f in result.get("flags", []) if f not in flags]


def run_paper_discovery(db: Session, doc: Document, limit: int = 40,
                        only_ids: set[str] | None = None) -> dict:
    refs = [r for r in doc.references if only_ids is None or r.id in only_ids]
    refs = refs[:limit]
    counts = {"matched": 0, "ambiguous": 0, "not_found": 0, "skipped": 0, "enhanced": 0}

    for ref in refs:
        if not ref.title and not ref.doi:
            counts["skipped"] += 1  # incomplete entry: nothing reliable to search with
            continue

        result = discover({"title": ref.title, "authors": ref.authors, "year": ref.year, "doi": ref.doi})
        _apply(ref, result, "crossref_openalex_europepmc")
        best = result.get("best")

        if result["status"] != "matched":
            enhanced = research_discovery.find_paper(
                title=ref.title, authors=ref.authors, year=ref.year, doi=ref.doi
            )
            if enhanced and enhanced.title:
                best = {
                    "title": enhanced.title,
                    "authors": enhanced.authors,
                    "year": enhanced.year,
                    "doi": enhanced.doi,
                    "url": enhanced.source_url or enhanced.url,
                    "journal": enhanced.journal,
                    "abstract": enhanced.abstract,
                    "openalex_id": enhanced.openalex_id,
                    "pdf_url": enhanced.pdf_url or enhanced.fulltext_url,
                    "xml_url": enhanced.xml_url,
                    "is_oa": enhanced.is_oa,
                    "sources": [enhanced.source],
                }
                ref.matching_status = "matched"
                ref.matching_confidence = enhanced.confidence or 0.9
                ref.flags = list(dict.fromkeys((ref.flags or []) + ["matched_via_" + enhanced.source]))
                counts["enhanced"] += 1

        if ref.matching_status == "matched" and best:
            ref.matched_title = best.get("title")
            ref.matched_authors = best.get("authors") or []
            ref.matched_year = best.get("year")
            ref.matched_doi = best.get("doi")
            ref.matched_source_url = (
                f"https://doi.org/{best['doi']}" if best.get("doi") else best.get("url")
            )
            ref.openalex_id = best.get("openalex_id")
            ref.publication_source = best.get("journal")
            ref.abstract = best.get("abstract") or ref.abstract
            ref.fulltext_url = best.get("pdf_url") or best.get("xml_url")
            # Full text is only confirmed by the retrieval stage.
            ref.fulltext_availability = "abstract_only" if ref.abstract else "none"
        else:
            ref.matched_title = ref.matched_doi = ref.matched_source_url = None
            ref.openalex_id = ref.publication_source = None
            ref.matched_authors, ref.matched_year = [], None
            ref.fulltext_availability = "none"

        counts[ref.matching_status if ref.matching_status in counts else "not_found"] += 1
        db.add(ref)
        db.commit()

    return {"total_references": len(doc.references), "considered": len(refs), **counts}
