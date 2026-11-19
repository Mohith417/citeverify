import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import upload as upload_module
from app.database import Base, get_db
from app.main import app

BODY = "Hypertension affects a large share of adults worldwide and remains a leading risk factor [1]. "


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


def test_extract_citations_endpoint(client, tmp_path):
    p = tmp_path / "paper.pdf"
    c = canvas.Canvas(str(p))
    y = 800
    for line in [BODY, BODY, "Another claim is made here and cited incorrectly [3].", BODY,
                 "References",
                 "[1] Smith J, Lee K. Blood pressure control in adults. Hypertension. 2020;5:1-9.",
                 "[2] Wang L. Salt intake and stroke risk. Lancet. 2019;3:10-20."]:
        c.drawString(40, y, line)
        y -= 16
    c.showPage()
    c.save()

    up = client.post("/api/documents/upload", files={"file": ("paper.pdf", p.read_bytes(), "application/pdf")})
    assert up.status_code == 200
    r = client.post(f"/api/documents/{up.json()['id']}/extract-citations")
    assert r.status_code == 200
    out = r.json()
    assert out["reference_section_found"] is True
    assert out["references_parsed"] == 2
    assert out["citations_found"] >= 3
    assert any(u["marker"] == "[3]" for u in out["unmatched_citations"])
    assert out["uncited_references"] == ["2"]
    # re-running must not duplicate references
    again = client.post(f"/api/documents/{up.json()['id']}/extract-citations").json()
    assert again["references_parsed"] == 2


def test_extract_404(client):
    assert client.post("/api/documents/nope/extract-citations").status_code == 404
