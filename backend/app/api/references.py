from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reference, Document
from ..schemas.claim_schema import ReferenceOut

router = APIRouter(prefix="/api/references", tags=["references"])


def _get_reference(db: Session, reference_id: str) -> Reference:
    ref = db.get(Reference, reference_id)
    if ref is None:
        raise HTTPException(status_code=404, detail="Reference not found.")
    return ref


@router.get("/{reference_id}", response_model=ReferenceOut)
def get_reference(reference_id: str, db: Session = Depends(get_db)):
    return _get_reference(db, reference_id)


@router.post("/{reference_id}/upload-source", response_model=ReferenceOut)
def upload_source_pdf(
    reference_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Allow user to manually upload a source PDF for a reference (fallback)."""
    ref = _get_reference(db, reference_id)

    # Validate file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted.")

    data = file.file.read()
    if not data or data.lstrip()[:5] != b"%PDF-":
        raise HTTPException(status_code=400, detail="File is not a valid PDF.")

    # Store the source PDF (in production, save to storage/uploads/sources/)
    # For now, record the filename in the reference's metadata
    ref.flags = (ref.flags or []) + ["source_uploaded"]
    db.add(ref)
    db.commit()
    db.refresh(ref)

    return ref