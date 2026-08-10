import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.contract import Contract

class Party(Base, UUIDPKMixin):
    __tablename__ = "parties"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)

    contract: Mapped["Contract"] = relationship(back_populates="parties")