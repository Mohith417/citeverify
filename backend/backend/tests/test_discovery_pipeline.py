from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.database import Base
from app.services import discovery_pipeline as dp

BEST = {"title": "Blood pressure control in adults", "authors": ["John Smith"], "year": 2020,
        "doi": "10.1234/abc.5", "url": "https://x.org", "journal": "Hypertension", "abstract": "An abstract.",
        "openalex_id": "https://openalex.org/W1", "pdf_url": "https://x.org/p.pdf", "xml_url": None}


def test_pipeline_updates_references(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = Session(engine)
    doc = models.Document(filename="a.pdf", stored_path="x")
    doc.references = [
        models.Reference(ref_label="1", reference_text="t", title="Blood pressure control in adults",
                         authors=["Smith J"], year=2020),
        models.Reference(ref_label="2", reference_text="junk", flags=["incomplete_reference"],
                         matching_status="incomplete"),
        models.Reference(ref_label="3", reference_text="t3", title="Another paper title here",
                         authors=["Lee K"], year=2019),
    ]
    s.add(doc)
    s.commit()

    def fake(ref):
        if ref["title"].startswith("Blood"):
            return {"status": "matched", "confidence": 0.95, "best": BEST, "candidates": [],
                    "flags": ["author_mismatch"]}
        return {"status": "ambiguous", "confidence": 0.6, "best": None,
                "candidates": [{"title": "x"}], "flags": []}

    monkeypatch.setattr(dp, "discover", fake)
    out = dp.run_paper_discovery(s, doc)
    assert out["matched"] == 1 and out["ambiguous"] == 1 and out["skipped"] == 1
    by = {r.ref_label: r for r in doc.references}
    assert by["1"].matching_status == "matched" and by["1"].matched_doi == "10.1234/abc.5"
    assert by["1"].fulltext_availability == "abstract_only" and "author_mismatch" in by["1"].flags
    assert by["1"].matched_source_url == "https://doi.org/10.1234/abc.5"
    assert by["3"].matching_status == "ambiguous" and by["3"].matched_doi is None
    assert by["2"].matching_status == "incomplete"
