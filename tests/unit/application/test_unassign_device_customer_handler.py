from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.device.unassign_device_customer import UnassignDeviceCustomerCommand, UnassignDeviceCustomerHandler
from app.domain.device import Device
from app.domain.exceptions import DeviceNotFoundError
from app.domain.value_objects import CustomerId, DeviceId, SerialNumber, TimeZone


def _make_assigned_device() -> Device:
    device = Device(id=DeviceId(uuid4()), serial_number=SerialNumber("SN-001"))
    device.customer_id = CustomerId(uuid4())
    device.timezone = TimeZone("Europe/Madrid")
    return device


def _make_unassigned_device() -> Device:
    return Device(id=DeviceId(uuid4()), serial_number=SerialNumber("SN-002"))


class TestUnassignDeviceCustomerHandler:
    async def test_unassigns_device_and_clears_timezone(self) -> None:
        device = _make_assigned_device()
        device_repo = AsyncMock()
        device_repo.get_by_id_for_update.return_value = device

        handler = UnassignDeviceCustomerHandler(device_repository=device_repo)
        result = await handler.handle(UnassignDeviceCustomerCommand(device_id=uuid4()))

        assert result.customer_id is None
        assert result.timezone is None
        device_repo.save.assert_awaited_once_with(result)

    async def test_idempotent_when_already_unassigned(self) -> None:
        device = _make_unassigned_device()
        device_repo = AsyncMock()
        device_repo.get_by_id_for_update.return_value = device

        handler = UnassignDeviceCustomerHandler(device_repository=device_repo)
        result = await handler.handle(UnassignDeviceCustomerCommand(device_id=uuid4()))

        assert result.customer_id is None
        device_repo.save.assert_awaited_once()

    async def test_raises_when_device_not_found(self) -> None:
        device_repo = AsyncMock()
        device_repo.get_by_id_for_update.return_value = None

        handler = UnassignDeviceCustomerHandler(device_repository=device_repo)
        with pytest.raises(DeviceNotFoundError):
            await handler.handle(UnassignDeviceCustomerCommand(device_id=uuid4()))

        device_repo.save.assert_not_awaited()
