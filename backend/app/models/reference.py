from sqlalchemy import Float, ForeignKey, JSON, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from ._common import new_id


class Reference(Base):
    __tablename__ = "references"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    ref_label: Mapped[str] = mapped_column(String(100), default="")  # "1" or "Smith 2023"
    reference_text: Mapped[str] = mapped_column(Text)  # original text as in bibliography
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    journal: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # discovery results (what we actually found, never invented)
    # pending | matched | ambiguous | not_found | incomplete
    matching_status: Mapped[str] = mapped_column(String(16), default="pending")
    matching_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_authors: Mapped[list] = mapped_column(JSON, default=list)
    matched_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matched_doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matched_source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    openalex_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    publication_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    # none | abstract_only | full_text
    fulltext_availability: Mapped[str] = mapped_column(String(16), default="none")
    fulltext_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # candidates kept when ambiguous so a human can choose
    candidates: Mapped[list] = mapped_column(JSON, default=list)
    # duplicate_reference | incorrect_doi | title_mismatch | author_mismatch ...
    flags: Mapped[list] = mapped_column(JSON, default=list)

    document = relationship("Document", back_populates="references")
    claim_links = relationship("ClaimReference", cascade="all, delete-orphan", back_populates="reference")
