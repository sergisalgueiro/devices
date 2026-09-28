from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.device.update_device_activation import (
    UpdateDeviceActivationCommand,
    UpdateDeviceActivationHandler,
)
from app.domain.device import Device
from app.domain.exceptions import DeviceNotFoundError
from app.domain.value_objects import CustomerId, DeviceId, IsActive, SerialNumber


def _make_device(*, is_active: bool = True) -> Device:
    return Device(
        id=DeviceId(uuid4()),
        serial_number=SerialNumber("SN-TEST-001"),
        customer_id=CustomerId(uuid4()),
        is_active=IsActive(is_active),
    )


class TestUpdateDeviceActivationHandler:
    async def test_activates_inactive_device(self) -> None:
        device = _make_device(is_active=False)
        repo = AsyncMock()
        repo.get_by_id.return_value = device

        handler = UpdateDeviceActivationHandler(device_repository=repo)
        await handler.handle(
            UpdateDeviceActivationCommand(device_id=device.id.value, is_active=True)
        )

        assert device.is_active.value is True
        repo.save.assert_awaited_once_with(device)

    async def test_deactivates_active_device(self) -> None:
        device = _make_device(is_active=True)
        repo = AsyncMock()
        repo.get_by_id.return_value = device

        handler = UpdateDeviceActivationHandler(device_repository=repo)
        await handler.handle(
            UpdateDeviceActivationCommand(device_id=device.id.value, is_active=False)
        )

        assert device.is_active.value is False
        repo.save.assert_awaited_once_with(device)

    async def test_idempotent_noop_on_same_state(self) -> None:
        device = _make_device(is_active=True)
        repo = AsyncMock()
        repo.get_by_id.return_value = device

        handler = UpdateDeviceActivationHandler(device_repository=repo)
        await handler.handle(
            UpdateDeviceActivationCommand(device_id=device.id.value, is_active=True)
        )

        assert device.is_active.value is True
        repo.save.assert_awaited_once_with(device)

    async def test_raises_when_device_not_found(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = None

        handler = UpdateDeviceActivationHandler(device_repository=repo)
        with pytest.raises(DeviceNotFoundError):
            await handler.handle(
                UpdateDeviceActivationCommand(device_id=uuid4(), is_active=True)
            )

        repo.save.assert_not_awaited()
