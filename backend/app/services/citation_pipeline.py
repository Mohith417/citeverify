"""Module 3: citation extraction, reference parsing and claim→reference mapping."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ..models import Document, Reference
from .citation_extractor import find_citations, map_citation, parse_references, split_reference_entries, surname
from .pdf_parser import split_body_and_references

NUM_MARKER = re.compile(r"^\[\s*(\d+)\s*\]$")
AY_MARKER = re.compile(r"\(?\s*([A-Z][A-Za-z'’\-]+)[^()]{0,40}?((?:19|20)\d{2})[a-z]?\s*\)?")


def run_citation_extraction(db: Session, doc: Document) -> dict:
    pages = [(p.page_number, p.text) for p in sorted(doc.pages, key=lambda p: p.page_number)]
    body, ref_text = split_body_and_references(pages)
    parsed = parse_references(split_reference_entries(ref_text)) if ref_text else []

    doc.references.clear()
    db.flush()
    for p in parsed:
        db.add(
            Reference(
                document_id=doc.id,
                ref_label=p.label,
                reference_text=p.text,
                title=p.title,
                authors=p.authors,
                year=p.year,
                doi=p.doi,
                flags=p.flags,
                matching_status="incomplete" if "incomplete_reference" in p.flags else "pending",
            )
        )

    citations_found = 0
    unmatched, ambiguous, cited = [], [], set()
    for page_no, text in body:
        for c in find_citations(text):
            citations_found += 1
            for m in map_citation(c, parsed):
                if m.status == "unmatched":
                    item = {"marker": c.marker, "page": page_no}
                    if item not in unmatched:
                        unmatched.append(item)
                else:
                    cited.add(m.ref_index)
                    if m.status == "ambiguous":
                        item = {"marker": c.marker, "page": page_no}
                        if item not in ambiguous:
                            ambiguous.append(item)
    db.commit()

    return {
        "reference_section_found": bool(ref_text),
        "references_parsed": len(parsed),
        "references_incomplete": sum("incomplete_reference" in p.flags for p in parsed),
        "references_duplicate": sum("duplicate_reference" in p.flags for p in parsed),
        "citations_found": citations_found,
        "unmatched_citations": unmatched,
        "ambiguous_citations": ambiguous,
        "uncited_references": [p.label for i, p in enumerate(parsed) if i not in cited],
        "references": [
            {"label": p.label, "title": p.title, "authors": p.authors, "year": p.year,
             "doi": p.doi, "flags": p.flags}
            for p in parsed
        ],
    }


def match_marker(marker: str, refs: list[Reference]) -> list[tuple[Reference, str]]:
    """Resolve one in-text marker to reference rows. Never guesses between rivals."""
    marker = (marker or "").strip()
    if not marker:
        return []

    numeric = NUM_MARKER.match(marker)
    numbers: list[int] = []
    if numeric:
        numbers = [int(numeric.group(1))]
    elif marker.startswith("[") and marker.endswith("]"):
        numbers = [int(n) for n in re.findall(r"\d+", marker)]

    if numbers:
        out = []
        for n in numbers:
            hits = [r for r in refs if r.ref_label == str(n)]
            if len(hits) == 1:
                out.append((hits[0], "matched"))
            elif len(hits) > 1:
                out.extend((h, "ambiguous") for h in hits)
        return out

    ay = AY_MARKER.search(marker)
    if not ay:
        return []
    author, year = ay.group(1).lower(), int(ay.group(2))
    hits = []
    for r in refs:
        if r.year != year or not r.authors:
            continue
        first = surname(r.authors[0])
        if first == author or first.endswith(" " + author) or first.startswith(author):
            hits.append(r)
    if len(hits) == 1:
        return [(hits[0], "matched")]
    if len(hits) > 1:
        return [(h, "ambiguous") for h in hits]
    return []
