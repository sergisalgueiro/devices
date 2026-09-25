from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.device.assign_device_customer import AssignDeviceCustomerCommand, AssignDeviceCustomerHandler
from app.domain.device import Device
from app.domain.exceptions import CustomerNotFoundError, DeviceNotFoundError
from app.domain.value_objects import CustomerId, DeviceId, SerialNumber


def _make_device() -> Device:
    return Device(id=DeviceId(uuid4()), serial_number=SerialNumber("SN-001"))


class TestAssignDeviceCustomerHandler:
    async def test_assigns_device_to_customer(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = _make_device()
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = AssignDeviceCustomerHandler(
            device_repository=device_repo, customer_repository=customer_repo
        )
        device = await handler.handle(
            AssignDeviceCustomerCommand(device_id=uuid4(), customer_id=customer_id)
        )

        assert device.customer_id == CustomerId(customer_id)
        assert device.timezone is None
        device_repo.save.assert_awaited_once_with(device)

    async def test_assigns_device_with_timezone(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = _make_device()
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = AssignDeviceCustomerHandler(
            device_repository=device_repo, customer_repository=customer_repo
        )
        device = await handler.handle(
            AssignDeviceCustomerCommand(
                device_id=uuid4(), customer_id=customer_id, timezone="Europe/Madrid"
            )
        )

        assert device.customer_id == CustomerId(customer_id)
        assert device.timezone is not None
        assert device.timezone.value == "Europe/Madrid"

    async def test_raises_when_device_not_found(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = None
        customer_repo = AsyncMock()

        handler = AssignDeviceCustomerHandler(
            device_repository=device_repo, customer_repository=customer_repo
        )
        with pytest.raises(DeviceNotFoundError):
            await handler.handle(
                AssignDeviceCustomerCommand(device_id=uuid4(), customer_id=uuid4())
            )

        device_repo.save.assert_not_awaited()

    async def test_raises_when_customer_not_found(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = _make_device()
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = None

        handler = AssignDeviceCustomerHandler(
            device_repository=device_repo, customer_repository=customer_repo
        )
        with pytest.raises(CustomerNotFoundError):
            await handler.handle(
                AssignDeviceCustomerCommand(device_id=uuid4(), customer_id=uuid4())
            )

        device_repo.save.assert_not_awaited()
