from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.application.device.create_device import CreateDeviceCommand, CreateDeviceHandler
from app.domain.device import Device
from app.domain.exceptions import CustomerNotFoundError, DomainValidationError, SerialNumberAlreadyExistsError
from app.domain.value_objects import CustomerId, DeviceId, SerialNumber


def _make_device(serial_number: str = "SN-EXISTING-001") -> Device:
    return Device(
        id=DeviceId(uuid4()),
        serial_number=SerialNumber(serial_number),
        customer_id=CustomerId(uuid4()),
    )


class TestCreateDeviceHandler:
    async def test_creates_device_and_returns_it(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = None
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = CreateDeviceHandler(device_repository=device_repo, customer_repository=customer_repo)
        device = await handler.handle(
            CreateDeviceCommand(serial_number="SN-001", customer_id=customer_id)
        )

        assert device.serial_number.value == "SN-001"
        assert device.customer_id.value == customer_id
        assert device.is_active is True
        device_repo.save.assert_awaited_once_with(device)

    async def test_creates_device_with_timezone(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = None
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = CreateDeviceHandler(device_repository=device_repo, customer_repository=customer_repo)
        device = await handler.handle(
            CreateDeviceCommand(serial_number="SN-001", customer_id=customer_id, timezone="Europe/Madrid")
        )

        assert device.timezone is not None
        assert device.timezone.value == "Europe/Madrid"

    async def test_raises_when_customer_not_found(self) -> None:
        device_repo = AsyncMock()
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = None

        handler = CreateDeviceHandler(device_repository=device_repo, customer_repository=customer_repo)
        with pytest.raises(CustomerNotFoundError):
            await handler.handle(
                CreateDeviceCommand(serial_number="SN-001", customer_id=uuid4())
            )

        device_repo.save.assert_not_awaited()

    async def test_raises_when_serial_number_already_exists(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = _make_device("SN-001")
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = CreateDeviceHandler(device_repository=device_repo, customer_repository=customer_repo)
        with pytest.raises(SerialNumberAlreadyExistsError):
            await handler.handle(
                CreateDeviceCommand(serial_number="SN-001", customer_id=customer_id)
            )

        device_repo.save.assert_not_awaited()

    async def test_raises_on_invalid_serial_number(self) -> None:
        customer_id = uuid4()
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = None
        customer_repo = AsyncMock()
        customer_repo.get_by_id.return_value = object()

        handler = CreateDeviceHandler(device_repository=device_repo, customer_repository=customer_repo)
        with pytest.raises(DomainValidationError):
            await handler.handle(
                CreateDeviceCommand(serial_number="", customer_id=customer_id)
            )

        device_repo.save.assert_not_awaited()
