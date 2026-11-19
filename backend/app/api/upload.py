from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Document, DocumentPage
from ..models._common import new_id
from ..schemas.document_schema import DocumentOut
from ..services.pdf_parser import PDFError, extract_pages, needs_ocr
from ..utils.validation import UploadError, read_limited, validate_pdf

router = APIRouter(prefix="/api/documents", tags=["documents"])
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads"


@router.post("/upload", response_model=DocumentOut)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        data = read_limited(file.file, settings.max_upload_mb * 1024 * 1024)
        validate_pdf(file.filename, data)
    except UploadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    doc_id = new_id()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{doc_id}.pdf"  # server-generated name, original is preserved untouched
    path.write_bytes(data)

    try:
        pages = extract_pages(path)
    except PDFError as e:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    scanned = needs_ocr(pages)
    doc = Document(
        id=doc_id,
        filename=Path(file.filename).name[:255],
        stored_path=str(path),
        page_count=len(pages),
        needs_ocr=scanned,
        processing_status="needs_review" if scanned else "uploaded",
        stage_message=(
            "This PDF appears to be scanned or image-only. OCR is required; no text was extracted."
            if scanned else "Uploaded and text extracted."
        ),
    )
    if not scanned:
        doc.pages = [DocumentPage(page_number=n, text=t) for n, t in pages]
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
