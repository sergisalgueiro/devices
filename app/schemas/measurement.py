from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import DomainResponseBase


class MeasurementIngestItem(BaseModel):
    """Schema for a single measurement within an ingestion request."""

    measurement_id: UUID = Field(description="Client-generated unique ID for idempotency")
    type: str = Field(min_length=1, max_length=100, description="Measurement type (e.g. 'temperature')")
    value: float = Field(description="Numeric measurement value")
    unit: str = Field(min_length=1, max_length=50, description="Unit of measurement (e.g. '°C')")
    timestamp: datetime = Field(description="UTC timestamp of the measurement")


class MeasurementResponse(DomainResponseBase):
    """Schema for a single measurement in a list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique measurement identifier")
    device_id: UUID = Field(description="ID of the device that produced this measurement")
    type: str = Field(description="Measurement type (e.g. 'temperature', 'energy')")
    value: float = Field(description="Numeric measurement value")
    unit: str = Field(description="Unit of measurement (e.g. '°C', 'kWh')")
    timestamp: datetime = Field(description="UTC timestamp when the measurement was recorded")


class PaginatedMeasurementsResponse(BaseModel):
    """Paginated list of measurements."""

    items: list[MeasurementResponse] = Field(description="Measurements on this page")
    next_cursor: str | None = Field(description="Opaque cursor to pass as `cursor` to retrieve the next page; null if no more pages")
    has_more: bool = Field(description="Whether additional pages exist")
