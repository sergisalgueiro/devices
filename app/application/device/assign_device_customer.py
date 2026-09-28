from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.domain.device import Device
from app.domain.exceptions import CustomerNotFoundError, DeviceNotFoundError
from app.domain.repositories import CustomerRepository, DeviceRepository
from app.domain.value_objects import CustomerId, DeviceId, TimeZone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssignDeviceCustomerCommand:
    """Command DTO for assigning a device to a customer."""

    device_id: UUID
    customer_id: UUID
    timezone: str | None = None


@dataclass
class AssignDeviceCustomerHandler:
    """Application handler for the AssignDeviceCustomerCommand use case."""

    device_repository: DeviceRepository
    customer_repository: CustomerRepository

    async def handle(self, command: AssignDeviceCustomerCommand) -> Device:
        """
        Assign a device to a customer, optionally setting a timezone.

        Raises:
            DeviceNotFoundError: if the device does not exist.
            CustomerNotFoundError: if the customer does not exist.
            DomainValidationError: if any field fails domain validation.
        """
        logger.debug("AssignDeviceCustomer: device_id=%s, customer_id=%s", command.device_id, command.customer_id)

        device_id = DeviceId(command.device_id)
        customer_id = CustomerId(command.customer_id)

        device = await self.device_repository.get_by_id_for_update(device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device with id {command.device_id!r} not found.")

        customer = await self.customer_repository.get_by_id(customer_id)
        if customer is None:
            raise CustomerNotFoundError(f"Customer with id {command.customer_id!r} not found.")

        device.assign_customer(
            customer_id,
            timezone=TimeZone(command.timezone) if command.timezone is not None else None,
        )

        await self.device_repository.save(device)
        logger.info("Device assigned: device_id=%s, customer_id=%s", command.device_id, command.customer_id)
        return device
