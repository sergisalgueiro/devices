from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.exceptions import DeviceAlreadyAssignedError
from app.domain.value_objects import (
    CreatedAt,
    DeviceId,
    DeviceStatus,
    CustomerId,
    IsActive,
    SerialNumber,
    TimeZone,
    UpdatedAt,
)


@dataclass
class Device:
    """Domain entity representing an IoT Device composed strictly of Value Objects."""

    serial_number: SerialNumber
    customer_id: CustomerId | None = None
    id: DeviceId = field(default_factory=DeviceId)
    status: DeviceStatus = field(default_factory=DeviceStatus)
    is_active: IsActive = field(default_factory=IsActive)
    timezone: TimeZone | None = None
    created_at: CreatedAt = field(default_factory=CreatedAt)
    updated_at: UpdatedAt = field(default_factory=UpdatedAt)

    def set_active(self, is_active: bool) -> None:
        """Update activation status. Idempotent no-op if already in the target state."""
        if self.is_active.value == is_active:
            return
        self.is_active = IsActive(is_active)
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

    def assign_customer(self, customer_id: CustomerId, timezone: TimeZone | None = None) -> None:
        """Assign device to a customer, optionally setting a timezone.

        Raises DeviceAlreadyAssignedError if already assigned to a different customer.
        Same-customer re-assignment (e.g. to update timezone) is accepted.
        """
        if self.customer_id is not None and self.customer_id != customer_id:
            raise DeviceAlreadyAssignedError(
                f"Device {self.id} is already assigned to customer {self.customer_id}. "
                f"Unassign it first before assigning to customer {customer_id}."
            )
        self.customer_id = customer_id
        self.timezone = timezone
        self.touch()

    def unassign_customer(self) -> None:
        """Remove customer assignment and clear timezone. Idempotent."""
        if self.customer_id is None:
            return
        self.customer_id = None
        self.timezone = None
        self.touch()

    def touch(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = UpdatedAt()
