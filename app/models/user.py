import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDPKMixin

class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    email_verified: Mapped[bool] = mapped_column(nullable=False, default=False)