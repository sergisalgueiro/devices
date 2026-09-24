from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class CustomerModel(Base):
    """SQLAlchemy ORM model for the customers table."""

    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    language: Mapped[str | None] = mapped_column(sa.String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(sa.String(2), nullable=True)
    timezone: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
