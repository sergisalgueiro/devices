from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions import DeviceNotFoundError
from app.domain.repositories import DeviceRepository


@dataclass(frozen=True)
class UpdateDeviceActivationCommand:
    """Command DTO for updating a device's activation status."""

    device_id: UUID
    is_active: bool


@dataclass
class UpdateDeviceActivationHandler:
    """Application handler for the UpdateDeviceActivationCommand use case."""

    device_repository: DeviceRepository

    async def handle(self, command: UpdateDeviceActivationCommand) -> None:
        """
        Update the activation status of the device with the given id.

        Raises:
            DeviceNotFoundError: if no device exists with that id.
        """
        device = await self.device_repository.get_by_id(command.device_id)
        if device is None:
            raise DeviceNotFoundError(
                f"Device with id {command.device_id!r} not found."
            )

        device.set_active(command.is_active)
        await self.device_repository.save(device)
