import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.clause import Clause
    from app.models.party import Party
    from app.models.reminder import Reminder


class FileType(enum.Enum):
    pdf = "pdf"
    docx = "docx"

class ContractStatus(enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    pending_review = "pending_review"
    completed = "completed"
    failed = "failed"

class Contract(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "contracts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )

    file_ref: Mapped[str] = mapped_column(nullable=False)
    original_filename: Mapped[str] = mapped_column(nullable=False)
    file_type: Mapped[FileType] = mapped_column(SAEnum(FileType), nullable=False)
    status: Mapped[ContractStatus] = mapped_column(SAEnum(ContractStatus), nullable=False, default=ContractStatus.uploaded)

    parties: Mapped[list["Party"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    clauses : Mapped[list["Clause"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )