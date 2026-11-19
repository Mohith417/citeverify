from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from ._common import new_id


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"))
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id", ondelete="CASCADE"))
    passage: Mapped[str] = mapped_column(Text)  # verbatim text from source
    paragraph_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_abstract_only: Mapped[bool] = mapped_column(Boolean, default=False)
    quote_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    claim = relationship("Claim", back_populates="evidence")
