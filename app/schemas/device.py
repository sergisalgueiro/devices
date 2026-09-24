from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceActivationUpdate(BaseModel):
    """Schema for updating a device's activation status."""

    is_active: bool = Field(description="Target activation status of the device")
