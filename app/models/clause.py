import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy import Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.contract import Contract

class ClauseType(enum.Enum):
    effective_date = "effective_date"
    renewal_date = "renewal_date"
    notice_period = "notice_period"
    termination_clause = "termination_clause"
    payment_terms = "payment_terms"

class Clause(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "clauses"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False, index=True
    )
    type: Mapped[ClauseType] = mapped_column(SAEnum(ClauseType), nullable=False)

    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    original_value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    source_text_span: Mapped[str] = mapped_column(nullable=False)

    is_corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    contract: Mapped["Contract"] = relationship(back_populates="clauses")