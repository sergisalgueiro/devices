from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.domain.device import Device
from app.domain.exceptions import CustomerNotFoundError, SerialNumberAlreadyExistsError
from app.domain.repositories import CustomerRepository, DeviceRepository
from app.domain.value_objects import CustomerId, SerialNumber, TimeZone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateDeviceCommand:
    """Command DTO for creating a new device."""

    serial_number: str
    customer_id: UUID
    timezone: str | None = None


@dataclass
class CreateDeviceHandler:
    """Application handler for the CreateDeviceCommand use case."""

    device_repository: DeviceRepository
    customer_repository: CustomerRepository

    async def handle(self, command: CreateDeviceCommand) -> Device:
        """
        Create a new device.

        Raises:
            CustomerNotFoundError: if the customer does not exist.
            SerialNumberAlreadyExistsError: if the serial number is already registered.
            DomainValidationError: if any field fails domain validation.
        """
        logger.debug("CreateDevice: serial_number=%s, customer_id=%s", command.serial_number, command.customer_id)

        customer = await self.customer_repository.get_by_id(command.customer_id)
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with id {command.customer_id!r} not found."
            )

        existing = await self.device_repository.get_by_serial_number(command.serial_number)
        if existing is not None:
            raise SerialNumberAlreadyExistsError(
                f"A device with serial number {command.serial_number!r} already exists."
            )

        device = Device(
            serial_number=SerialNumber(command.serial_number),
            customer_id=CustomerId(command.customer_id),
            timezone=TimeZone(command.timezone) if command.timezone is not None else None,
        )

        await self.device_repository.save(device)
        logger.info("Device created: id=%s, serial_number=%s", device.id.value, command.serial_number)
        return device
