from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from app.schemas.base import DomainResponseBase


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


class DeviceResponse(DomainResponseBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique device identifier")
    serial_number: str = Field(description="Unique device serial number")
    customer_id: UUID | None = Field(description="ID of the assigned customer; null if unassigned")
    status: str = Field(description="Device lifecycle status (e.g. 'unassigned', 'assigned')")
    is_active: bool = Field(description="Whether the device is active and can ingest measurements")
    timezone: str | None = Field(default=None, description="IANA Time Zone identifier assigned to this device")
    created_at: datetime = Field(description="UTC timestamp when the device was registered")
    updated_at: datetime = Field(description="UTC timestamp of the last update")
