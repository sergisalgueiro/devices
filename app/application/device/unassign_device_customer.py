from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.domain.device import Device
from app.domain.exceptions import DeviceNotFoundError
from app.domain.repositories import DeviceRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnassignDeviceCustomerCommand:
    """Command DTO for unassigning a device from its current customer."""

    device_id: UUID


@dataclass
class UnassignDeviceCustomerHandler:
    """Application handler for the UnassignDeviceCustomerCommand use case."""

    device_repository: DeviceRepository

    async def handle(self, command: UnassignDeviceCustomerCommand) -> Device:
        """
        Unassign a device from its current customer and clear its timezone. Idempotent.

        Raises:
            DeviceNotFoundError: if the device does not exist.
        """
        logger.debug("UnassignDeviceCustomer: device_id=%s", command.device_id)

        device = await self.device_repository.get_by_id(command.device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device with id {command.device_id!r} not found.")

        device.unassign_customer()

        await self.device_repository.save(device)
        logger.info("Device unassigned: device_id=%s", command.device_id)
        return device
