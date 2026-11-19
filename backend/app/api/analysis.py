from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document
from ..schemas.document_schema import StatusOut

router = APIRouter(prefix="/api/documents", tags=["analysis"])


@router.get("/{document_id}/status", response_model=StatusOut)
def get_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc
