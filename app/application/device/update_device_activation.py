from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.domain.exceptions import DeviceNotFoundError
from app.domain.repositories import DeviceRepository

logger = logging.getLogger(__name__)


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
        logger.debug("UpdateDeviceActivation: device_id=%s, is_active=%s", command.device_id, command.is_active)

        device = await self.device_repository.get_by_id(command.device_id)
        if device is None:
            raise DeviceNotFoundError(
                f"Device with id {command.device_id!r} not found."
            )

        old_state = device.is_active
        device.set_active(command.is_active)
        await self.device_repository.save(device)

        if old_state != command.is_active:
            logger.info("Device %s activation changed: %s -> %s", command.device_id, old_state, command.is_active)
        else:
            logger.debug("Device %s already in target state: is_active=%s", command.device_id, command.is_active)
