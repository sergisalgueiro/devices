from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.device.create_device import CreateDeviceCommand, CreateDeviceHandler
from app.domain.exceptions import DomainValidationError, SerialNumberAlreadyExistsError
from app.domain.device import Device
from app.domain.value_objects import DeviceId, SerialNumber
from uuid import uuid4


def _make_device(serial_number: str = "SN-EXISTING-001") -> Device:
    return Device(id=DeviceId(uuid4()), serial_number=SerialNumber(serial_number))


class TestCreateDeviceHandler:
    async def test_creates_device_without_customer(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = None

        handler = CreateDeviceHandler(device_repository=device_repo)
        device = await handler.handle(CreateDeviceCommand(serial_number="SN-001"))

        assert device.serial_number.value == "SN-001"
        assert device.customer_id is None
        assert device.timezone is None
        assert device.is_active is True
        device_repo.save.assert_awaited_once_with(device)

    async def test_raises_when_serial_number_already_exists(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = _make_device("SN-001")

        handler = CreateDeviceHandler(device_repository=device_repo)
        with pytest.raises(SerialNumberAlreadyExistsError):
            await handler.handle(CreateDeviceCommand(serial_number="SN-001"))

        device_repo.save.assert_not_awaited()

    async def test_raises_on_invalid_serial_number(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_serial_number.return_value = None

        handler = CreateDeviceHandler(device_repository=device_repo)
        with pytest.raises(DomainValidationError):
            await handler.handle(CreateDeviceCommand(serial_number=""))

        device_repo.save.assert_not_awaited()
