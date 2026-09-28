from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.device import Device
from app.domain.exceptions import SerialNumberAlreadyExistsError
from app.domain.repositories import DeviceRepository
from app.domain.value_objects import SerialNumber

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateDeviceCommand:
    """Command DTO for creating a new device."""

    serial_number: str


@dataclass
class CreateDeviceHandler:
    """Application handler for the CreateDeviceCommand use case."""

    device_repository: DeviceRepository

    async def handle(self, command: CreateDeviceCommand) -> Device:
        """
        Create a new device without a customer assignment.

        Raises:
            SerialNumberAlreadyExistsError: if the serial number is already registered.
            DomainValidationError: if any field fails domain validation.
        """
        logger.debug("CreateDevice: serial_number=%s", command.serial_number)

        serial_number = SerialNumber(command.serial_number)
        existing = await self.device_repository.get_by_serial_number(serial_number)
        if existing is not None:
            raise SerialNumberAlreadyExistsError(
                f"A device with serial number {command.serial_number!r} already exists."
            )

        device = Device(serial_number=serial_number)

        await self.device_repository.save(device)
        logger.info("Device created: id=%s, serial_number=%s", device.id.value, command.serial_number)
        return device
