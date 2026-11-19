from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from ._common import new_id, utcnow


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # uploaded | extracting | searching_references | retrieving_evidence |
    # comparing_claims | generating_report | completed | failed | needs_review
    processing_status: Mapped[str] = mapped_column(String(32), default="uploaded")
    stage_message: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_ocr: Mapped[bool] = mapped_column(Boolean, default=False)

    pages = relationship("DocumentPage", cascade="all, delete-orphan", back_populates="document")
    claims = relationship("Claim", cascade="all, delete-orphan", back_populates="document")
    references = relationship("Reference", cascade="all, delete-orphan", back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, default="")

    document = relationship("Document", back_populates="pages")
