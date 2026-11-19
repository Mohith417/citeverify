from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document
from ..schemas.claim_schema import ReferenceOut
from ..schemas.document_schema import StatusOut
from ..services.citation_pipeline import run_citation_extraction
from ..services.discovery_pipeline import run_paper_discovery

router = APIRouter(prefix="/api/documents", tags=["analysis"])


def _get_doc(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.get("/{document_id}/status", response_model=StatusOut)
def get_status(document_id: str, db: Session = Depends(get_db)):
    return _get_doc(db, document_id)


@router.post("/{document_id}/extract-citations")
def extract_citations(document_id: str, db: Session = Depends(get_db)):
    # development endpoint; becomes one stage of /analyze in a later step
    doc = _get_doc(db, document_id)
    if doc.needs_ocr:
        raise HTTPException(status_code=400, detail="Scanned PDF: OCR is required before analysis.")
    return run_citation_extraction(db, doc)


@router.post("/{document_id}/discover-papers")
def discover_papers(document_id: str, db: Session = Depends(get_db)):
    # development endpoint; becomes one stage of /analyze in a later step
    doc = _get_doc(db, document_id)
    if not doc.references:
        raise HTTPException(status_code=400, detail="No references found. Run extract-citations first.")
    summary = run_paper_discovery(db, doc)
    refs = [ReferenceOut.model_validate(r) for r in doc.references]
    return {"summary": summary, "references": [r.model_dump(mode="json") for r in refs]}
