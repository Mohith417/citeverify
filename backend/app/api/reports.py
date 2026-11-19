from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from ..database import get_db
from ..models import Document
from ..services import generate_report

router = APIRouter(prefix="/api/documents", tags=["reports"])


@router.get("/{document_id}/report")
def download_report(document_id: str, db: Session = Depends(get_db)):
    """Generate and download a PDF verification report."""
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    output_dir = Path(__file__).resolve().parents[2] / "storage" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{document_id}.pdf"

    try:
        generate_report(db, document_id, str(output_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    if not output_path.exists():
        raise HTTPException(status_code=500, detail="Report file was not created.")

    return FileResponse(
        path=str(output_path),
        media_type="application/pdf",
        filename=f"citeverify_report_{document_id[:8]}.pdf",
    )