import io

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import upload as upload_module
from app.database import Base, get_db
from app.main import app
from app.services.pdf_parser import extract_pages, needs_ocr, split_body_and_references

LONG = "Hypertension affects a large share of adults worldwide and remains a leading risk factor [1]. "


def make_pdf(path, pages):
    c = canvas.Canvas(str(path))
    for lines in pages:
        y = 800
        for line in lines:
            c.drawString(40, y, line)
            y -= 16
        c.showPage()
    c.save()


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    monkeypatch.setattr(upload_module, "UPLOAD_DIR", tmp_path / "up")
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_extract_pages_and_references(tmp_path):
    p = tmp_path / "t.pdf"
    make_pdf(p, [[LONG, LONG, LONG], [LONG, "References", "[1] Smith J. Blood pressure study. 2020."]])
    pages = extract_pages(p)
    assert [n for n, _ in pages] == [1, 2]
    assert not needs_ocr(pages)
    body, refs = split_body_and_references(pages)
    assert "Smith J." in refs
    assert "Smith J." not in " ".join(t for _, t in body)


def test_scanned_pdf_detected(tmp_path):
    p = tmp_path / "blank.pdf"
    make_pdf(p, [[], []])
    assert needs_ocr(extract_pages(p))


def test_upload_ok(client, tmp_path):
    p = tmp_path / "ok.pdf"
    make_pdf(p, [[LONG] * 3, [LONG] * 3])
    r = client.post("/api/documents/upload", files={"file": ("ok.pdf", p.read_bytes(), "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["page_count"] == 2 and body["needs_ocr"] is False
    s = client.get(f"/api/documents/{body['id']}/status")
    assert s.status_code == 200 and s.json()["processing_status"] == "uploaded"


def test_upload_scanned_flagged(client, tmp_path):
    p = tmp_path / "b.pdf"
    make_pdf(p, [[]])
    r = client.post("/api/documents/upload", files={"file": ("b.pdf", p.read_bytes(), "application/pdf")})
    assert r.status_code == 200 and r.json()["needs_ocr"] is True
    assert r.json()["processing_status"] == "needs_review"


def test_upload_rejects_bad_files(client):
    r = client.post("/api/documents/upload", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 400
    r = client.post("/api/documents/upload", files={"file": ("x.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 400


def test_status_404(client):
    assert client.get("/api/documents/nope/status").status_code == 404
