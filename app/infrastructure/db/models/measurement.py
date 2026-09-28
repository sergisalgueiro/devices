from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class MeasurementModel(Base):
    """SQLAlchemy ORM model for the measurements table."""

    __tablename__ = "measurements"
    # Composite index serves the canonical list query:
    #   WHERE device_id = :id  ORDER BY timestamp, id
    # The leading device_id column handles the filter; timestamp + id provide a
    # pre-sorted, tiebreaker-stable order that cursor pagination can seek into
    # without a filesort.  The single-column ix_measurements_device_id index is
    # intentionally removed — it is fully subsumed by this composite index.
    __table_args__ = (
        sa.Index("ix_measurements_device_id_timestamp_id", "device_id", "timestamp", "id"),
    )

    id: Mapped[UUID] = mapped_column(sa.UUID(as_uuid=True), primary_key=True)
    device_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    value: Mapped[float] = mapped_column(sa.Float, nullable=False)
    unit: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
