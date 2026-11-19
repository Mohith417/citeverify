from sqlalchemy.orm import Session

from ..models import Document, Reference
from .citation_extractor import find_citations, map_citation, parse_references, split_reference_entries
from .pdf_parser import split_body_and_references


def run_citation_extraction(db: Session, doc: Document) -> dict:
    pages = [(p.page_number, p.text) for p in sorted(doc.pages, key=lambda p: p.page_number)]
    body, ref_text = split_body_and_references(pages)
    parsed = parse_references(split_reference_entries(ref_text)) if ref_text else []

    # re-running replaces the previous result
    doc.references.clear()
    db.flush()
    for p in parsed:
        db.add(Reference(
            document_id=doc.id, ref_label=p.label, reference_text=p.text, title=p.title,
            authors=p.authors, year=p.year, doi=p.doi, flags=p.flags,
            matching_status="incomplete" if "incomplete_reference" in p.flags else "pending",
        ))

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
