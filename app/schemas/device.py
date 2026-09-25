from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_extra_types.timezone_name import TimeZoneName


class DeviceActivationUpdate(BaseModel):
    """Schema for updating a device's activation status."""

    is_active: bool = Field(description="Target activation status of the device")


class DeviceCreate(BaseModel):
    """Schema for creating a new device."""

    serial_number: str = Field(..., min_length=1, max_length=100, description="Unique device serial number")


class AssignCustomerRequest(BaseModel):
    """Schema for assigning a device to a customer."""

    customer_id: UUID = Field(..., description="ID of the customer to assign this device to")
    timezone: TimeZoneName | None = Field(
        default=None,
        description="IANA Time Zone identifier (e.g., 'Europe/Madrid', 'UTC')",
    )


class DeviceResponse(BaseModel):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serial_number: str
    customer_id: UUID | None
    status: str
    is_active: bool
    timezone: str | None = None
    created_at: datetime
    updated_at: datetime

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
