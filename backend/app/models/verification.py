from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from ._common import new_id, utcnow


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), unique=True)
    # supported | partially_supported | unsupported | contradictory |
    # potentially_outdated | insufficient_evidence
    verdict: Mapped[str] = mapped_column(String(32))
    explanation: Mapped[str] = mapped_column(Text, default="")
    key_supporting_facts: Mapped[list] = mapped_column(JSON, default=list)
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    # low | medium | high  (strength of evidence, not statistical certainty)
    confidence_level: Mapped[str] = mapped_column(String(8), default="low")
    confidence_reason: Mapped[str] = mapped_column(Text, default="")
    # full_text | abstract_only | none
    evidence_basis: Mapped[str] = mapped_column(String(16), default="none")
    needs_human_review: Mapped[bool] = mapped_column(Boolean, default=True)
    review_reasons: Mapped[list] = mapped_column(JSON, default=list)
    # pending | confirmed | overridden
    reviewed_status: Mapped[str] = mapped_column(String(16), default="pending")
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    claim = relationship("Claim", back_populates="verification")
    history = relationship("ReviewEvent", cascade="all, delete-orphan", back_populates="verification")


class ReviewEvent(Base):
    # review history: every human action on a verdict is logged
    __tablename__ = "review_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    verification_id: Mapped[str] = mapped_column(ForeignKey("verifications.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(32))  # confirmed | overridden | note
    previous_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    verification = relationship("Verification", back_populates="history")
