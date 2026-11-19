from sqlalchemy.orm import Session

from ..models import Document
from .paper_search import discover

DISCOVERY_FLAGS = {"doi_not_found", "doi_mismatch", "title_mismatch", "author_mismatch",
                   "year_mismatch", "title_not_cross_checked"}


def run_paper_discovery(db: Session, doc: Document, limit: int = 60) -> dict:
    refs = list(doc.references)[:limit]
    counts = {"matched": 0, "ambiguous": 0, "not_found": 0, "skipped": 0}
    for r in refs:
        if not r.title and not r.doi:
            counts["skipped"] += 1  # incomplete entry: nothing to search with
            continue
        res = discover({"title": r.title, "authors": r.authors, "year": r.year, "doi": r.doi})
        kept = [f for f in (r.flags or []) if f not in DISCOVERY_FLAGS]
        r.flags = kept + [f for f in res["flags"] if f not in kept]
        r.matching_status = res["status"]
        r.matching_confidence = res["confidence"]
        r.candidates = res["candidates"]
        best = res["best"]
        if res["status"] == "matched" and best:
            r.matched_title = best["title"]
            r.matched_authors = best["authors"]
            r.matched_year = best["year"]
            r.matched_doi = best["doi"]
            r.matched_source_url = f"https://doi.org/{best['doi']}" if best["doi"] else best["url"]
            r.openalex_id = best["openalex_id"]
            r.publication_source = best["journal"]
            r.abstract = best["abstract"]
            r.fulltext_url = best["pdf_url"] or best["xml_url"]
            # only an abstract is known at this stage; full text is confirmed after retrieval
            r.fulltext_availability = "abstract_only" if best["abstract"] else "none"
        else:
            # ambiguous / not found: never silently accept a match
            r.matched_title = r.matched_doi = r.matched_source_url = r.openalex_id = None
            r.publication_source = r.abstract = r.fulltext_url = None
            r.matched_authors, r.matched_year = [], None
            r.fulltext_availability = "none"
        counts[res["status"]] += 1
        db.commit()
    return {"total_references": len(doc.references), "processed": len(refs) - counts["skipped"], **counts}
