from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class DeviceModel(Base):
    """SQLAlchemy ORM model for the devices table."""

    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    serial_number: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    customer_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    timezone: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
