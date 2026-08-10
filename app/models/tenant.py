from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin



class Tenant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(nullable=False)
    api_key_hash: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    notification_email: Mapped[str | None] = mapped_column(nullable=True)