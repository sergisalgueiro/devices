from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.value_objects import (
    CreatedAt,
    DeviceId,
    DeviceStatus,
    CustomerId,
    SerialNumber,
    TimeZone,
    UpdatedAt,
)


@dataclass
class Device:
    """Domain entity representing an IoT Device composed strictly of Value Objects."""

    serial_number: SerialNumber
    customer_id: CustomerId
    id: DeviceId = field(default_factory=DeviceId)
    status: DeviceStatus = field(default_factory=DeviceStatus)
    is_active: bool = True
    timezone: TimeZone | None = None
    created_at: CreatedAt = field(default_factory=CreatedAt)
    updated_at: UpdatedAt = field(default_factory=UpdatedAt)


    def set_active(self, is_active: bool) -> None:
        """Update activation status. Idempotent no-op if already in the target state."""
        if self.is_active == is_active:
            return
        self.is_active = is_active
        self.touch()

    def update_status(self, new_status: DeviceStatus) -> None:
        """Update the device status and refresh the updated_at timestamp."""
        self.status = new_status
        self.touch()

    def connect(self) -> None:
        """Mark the IoT device as online/connected."""
        self.update_status(DeviceStatus.online())

    def disconnect(self) -> None:
        """Mark the IoT device as offline/disconnected."""
        self.update_status(DeviceStatus.offline())

    def decommission(self) -> None:
        """Decommission the IoT device."""
        self.update_status(DeviceStatus.decommissioned())

    def reassign_customer(self, new_customer_id: CustomerId) -> None:
        """Reassign device to another customer and refresh the updated_at timestamp."""
        self.customer_id = new_customer_id
        self.touch()

    def set_timezone(self, new_timezone: TimeZone | None) -> None:
        """Update the device timezone and refresh the updated_at timestamp."""
        self.timezone = new_timezone
        self.touch()


    def touch(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = UpdatedAt()
