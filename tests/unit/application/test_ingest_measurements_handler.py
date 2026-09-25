from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.measurement.ingest_measurements import (
    IngestMeasurementsCommand,
    IngestMeasurementsHandler,
    MeasurementItem,
)
from app.domain.device import Device
from app.domain.exceptions import DeviceNotFoundError, InactiveDeviceError
from app.domain.measurement import Measurement
from app.domain.value_objects import CustomerId, DeviceId, SerialNumber


def _make_device(*, is_active: bool = True) -> Device:
    return Device(
        id=DeviceId(uuid4()),
        serial_number=SerialNumber("SN-TEST-001"),
        customer_id=CustomerId(uuid4()),
        is_active=is_active,
    )


def _make_measurement_item() -> MeasurementItem:
    return MeasurementItem(
        measurement_id=uuid4(),
        type="temperature",
        value=22.5,
        unit="°C",
        timestamp=datetime.now(timezone.utc),
    )


class TestIngestMeasurementsHandler:
    async def test_ingests_measurements_for_active_device(self) -> None:
        """Happy path: active device, batch of measurements → calls save_batch, returns count."""
        device = _make_device(is_active=True)
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = device
        measurement_repo = AsyncMock()
        measurement_repo.save_batch.return_value = 2

        handler = IngestMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        items = [_make_measurement_item(), _make_measurement_item()]
        result = await handler.handle(
            IngestMeasurementsCommand(device_id=device.id.value, measurements=items)
        )

        assert result == 2
        measurement_repo.save_batch.assert_awaited_once()
        batch_arg = measurement_repo.save_batch.call_args[0][0]
        assert len(batch_arg) == 2
        assert all(isinstance(m, Measurement) for m in batch_arg)

    async def test_raises_when_device_not_found(self) -> None:
        """Device doesn't exist → DeviceNotFoundError, save_batch never called."""
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = None
        measurement_repo = AsyncMock()

        handler = IngestMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        with pytest.raises(DeviceNotFoundError):
            await handler.handle(
                IngestMeasurementsCommand(
                    device_id=uuid4(),
                    measurements=[_make_measurement_item()],
                )
            )

        measurement_repo.save_batch.assert_not_awaited()

    async def test_raises_when_device_is_inactive(self) -> None:
        """Device exists but is_active=False → InactiveDeviceError, save_batch never called."""
        device = _make_device(is_active=False)
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = device
        measurement_repo = AsyncMock()

        handler = IngestMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        with pytest.raises(InactiveDeviceError):
            await handler.handle(
                IngestMeasurementsCommand(
                    device_id=device.id.value,
                    measurements=[_make_measurement_item()],
                )
            )

        measurement_repo.save_batch.assert_not_awaited()

    async def test_empty_batch_returns_zero(self) -> None:
        """Empty measurement list → save_batch called with [], returns 0."""
        device = _make_device(is_active=True)
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = device
        measurement_repo = AsyncMock()
        measurement_repo.save_batch.return_value = 0

        handler = IngestMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        result = await handler.handle(
            IngestMeasurementsCommand(device_id=device.id.value, measurements=[])
        )

        assert result == 0
        measurement_repo.save_batch.assert_awaited_once_with([])

    async def test_converts_primitives_to_value_objects(self) -> None:
        """Verifies the handler constructs domain Measurement entities with proper VOs."""
        device = _make_device(is_active=True)
        device_repo = AsyncMock()
        device_repo.get_by_id.return_value = device
        measurement_repo = AsyncMock()
        measurement_repo.save_batch.return_value = 1

        item = _make_measurement_item()
        handler = IngestMeasurementsHandler(
            device_repository=device_repo,
            measurement_repository=measurement_repo,
        )
        await handler.handle(
            IngestMeasurementsCommand(device_id=device.id.value, measurements=[item])
        )

        batch_arg = measurement_repo.save_batch.call_args[0][0]
        assert len(batch_arg) == 1
        m: Measurement = batch_arg[0]
        assert m.id.value == item.measurement_id
        assert m.device_id.value == device.id.value
        assert m.type.value == item.type
        assert m.value.value == item.value
        assert m.unit.value == item.unit
        assert m.timestamp.value == item.timestamp
