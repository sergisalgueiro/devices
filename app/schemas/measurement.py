from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MeasurementIngestItem(BaseModel):
    """Schema for a single measurement within an ingestion request."""

    measurement_id: UUID = Field(description="Client-generated unique ID for idempotency")
    type: str = Field(min_length=1, max_length=100, description="Measurement type (e.g. 'temperature')")
    value: float = Field(description="Numeric measurement value")
    unit: str = Field(min_length=1, max_length=50, description="Unit of measurement (e.g. '°C')")
    timestamp: datetime = Field(description="UTC timestamp of the measurement")


class MeasurementResponse(BaseModel):
    """Schema for a single measurement in a list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    type: str
    value: float
    unit: str
    timestamp: datetime

    @model_validator(mode="before")
    @classmethod
    def unwrap_value_objects(cls, data: Any) -> Any:
        """Unwrap Value Objects when validating from domain entity objects."""
        if hasattr(data, "__dataclass_fields__"):
            return {
                field_name: getattr(field_val, "value", field_val)
                for field_name, field_val in (
                    (f, getattr(data, f)) for f in data.__dataclass_fields__
                )
            }
        return data


class PaginatedMeasurementsResponse(BaseModel):
    """Paginated list of measurements."""

    items: list[MeasurementResponse]
    next_cursor: str | None
    has_more: bool
