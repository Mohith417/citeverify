import pytest

from app.services import paper_search as ps

REF = {"title": "Blood pressure control in adults", "authors": ["Smith J", "Lee K"],
       "year": 2020, "doi": "10.1234/abc.5"}


def cr(title, doi, year=2020, authors=(("John", "Smith"), ("Kim", "Lee"))):
    return {"title": [title], "DOI": doi, "issued": {"date-parts": [[year]]},
            "author": [{"given": g, "family": f} for g, f in authors],
            "container-title": ["Hypertension"], "URL": f"https://doi.org/{doi}"}


class Fake:
    def __init__(self):
        self.doi = {}          # doi -> crossref item
        self.search = []       # crossref search items
        self.oa = {}           # doi -> openalex work
        self.oa_search = []

    def __call__(self, url, params=None, retries=2):
        if url.startswith(ps.CROSSREF + "/works/"):
            d = url[len(ps.CROSSREF + "/works/"):]
            return (200, {"message": self.doi[d]}) if d in self.doi else (404, None)
        if url == ps.CROSSREF + "/works":
            return 200, {"message": {"items": self.search}}
        if url.startswith(ps.EPMC):
            return 200, {"resultList": {"result": []}}
        if url.startswith(ps.OPENALEX + "/works/doi:"):
            d = url[len(ps.OPENALEX + "/works/doi:"):]
            return (200, self.oa[d]) if d in self.oa else (404, None)
        if url == ps.OPENALEX + "/works":
            return 200, {"results": self.oa_search}
        raise AssertionError(url)


@pytest.fixture
def fake(monkeypatch):
    f = Fake()
    monkeypatch.setattr(ps, "fetch_json", f)
    return f


def test_match_by_doi_and_enrich(fake):
    fake.doi["10.1234/abc.5"] = cr("Blood pressure control in adults", "10.1234/abc.5")
    fake.oa["10.1234/abc.5"] = {
        "display_name": "Blood pressure control in adults", "doi": "https://doi.org/10.1234/abc.5",
        "id": "https://openalex.org/W1", "abstract_inverted_index": {"Salt": [0], "reduces": [1], "pressure": [2]},
        "best_oa_location": {"pdf_url": "https://example.org/p.pdf", "landing_page_url": "https://example.org/p"},
        "open_access": {"is_oa": True}}
    r = ps.discover(REF)
    assert r["status"] == "matched" and r["confidence"] >= 0.9
    assert r["best"]["abstract"] == "Salt reduces pressure"
    assert r["best"]["pdf_url"] == "https://example.org/p.pdf"
    assert r["best"]["openalex_id"] == "https://openalex.org/W1"


def test_wrong_doi_flagged_and_title_fallback(fake):
    fake.doi["10.1234/abc.5"] = cr("Ocean currents of the northern Pacific", "10.1234/abc.5", authors=(("A", "Other"),))
    fake.search = [cr("Blood pressure control in adults", "10.9999/right.1")]
    r = ps.discover(REF)
    assert "doi_mismatch" in r["flags"]
    assert r["status"] == "matched" and r["best"]["doi"] == "10.9999/right.1"


def test_doi_not_found_flag(fake):
    r = ps.discover(REF)
    assert "doi_not_found" in r["flags"] and r["status"] == "not_found"


def test_ambiguous_never_guessed(fake):
    ref = dict(REF, doi=None)
    fake.search = [cr("Blood pressure control in adults", "10.1/preprint"),
                   cr("Blood pressure control in adults", "10.1/published")]
    r = ps.discover(ref)
    assert r["status"] == "ambiguous" and r["best"] is None and len(r["candidates"]) == 2


def test_similar_title_not_auto_accepted(fake):
    ref = dict(REF, doi=None)
    fake.search = [cr("Blood pressure control in elderly adults with diabetes", "10.2/x")]
    r = ps.discover(ref)
    assert r["status"] != "matched"


def test_author_mismatch_flag(fake):
    ref = dict(REF, doi=None)
    fake.search = [cr("Blood pressure control in adults", "10.3/y", authors=(("Zed", "Quill"),))]
    r = ps.discover(ref)
    assert r["status"] == "matched" and "author_mismatch" in r["flags"]


def test_host_restriction():
    with pytest.raises(ValueError):
        ps.fetch_json("http://evil.example.com/x")


def test_parsers():
    assert ps.abstract_from_inverted({"b": [1], "a": [0]}) == "a b"
    assert ps.strip_tags("<jats:p>Hello &amp; <b>world</b></jats:p>") == "Hello & world"
