from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from ._common import new_id


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    claim_text: Mapped[str] = mapped_column(Text)  # exact original wording, never rewritten
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    citation_markers: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["[1]", "(Smith, 2023)"]
    # factual | numerical | finding | statistical | conclusion | assertion
    claim_category: Mapped[str] = mapped_column(String(32), default="factual")
    # flags such as "missing_citation"
    flags: Mapped[list] = mapped_column(JSON, default=list)

    document = relationship("Document", back_populates="claims")
    reference_links = relationship("ClaimReference", cascade="all, delete-orphan", back_populates="claim")
    evidence = relationship("Evidence", cascade="all, delete-orphan", back_populates="claim")
    verification = relationship("Verification", cascade="all, delete-orphan", uselist=False, back_populates="claim")


class ClaimReference(Base):
    # many-to-many: one claim can cite several references and vice versa
    __tablename__ = "claim_references"

    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"), primary_key=True)
    marker: Mapped[str] = mapped_column(String(100), default="")
    # matched | ambiguous | unmatched
    match_status: Mapped[str] = mapped_column(String(16), default="matched")

    claim = relationship("Claim", back_populates="reference_links")
    reference = relationship("Reference", back_populates="claim_links")
