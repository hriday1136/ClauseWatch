import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.contract import Contract

class Reminder(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "reminders"
    __table_args__ = (
        UniqueConstraint("clause_id", "threshold_days", name="uq_reminder_clause_threshold"),
    )

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False, index=True
    )
    clause_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False, index=True
    )

    trigger_date: Mapped[date] = mapped_column(Date, nullable=False)
    threshold_days: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="reminders")