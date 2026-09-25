from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.exceptions import DeviceNotFoundError, InactiveDeviceError
from app.domain.measurement import Measurement
from app.domain.repositories import DeviceRepository, MeasurementRepository
from app.domain.value_objects import (
    DeviceId,
    MeasurementId,
    MeasurementType,
    MeasurementUnit,
    MeasurementValue,
    Timestamp,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MeasurementItem:
    """A single measurement within the ingestion command."""

    measurement_id: UUID
    type: str
    value: float
    unit: str
    timestamp: datetime


@dataclass(frozen=True)
class IngestMeasurementsCommand:
    """Command DTO for ingesting a batch of measurements for a device."""

    device_id: UUID
    measurements: list[MeasurementItem]


@dataclass
class IngestMeasurementsHandler:
    """Application handler for the IngestMeasurementsCommand use case."""

    device_repository: DeviceRepository
    measurement_repository: MeasurementRepository

    async def handle(self, command: IngestMeasurementsCommand) -> int:
        """
        Ingest a batch of measurements for the given device.

        Raises:
            DeviceNotFoundError: if the device does not exist.
            InactiveDeviceError: if the device is not active.

        Returns:
            The number of newly persisted measurements.
        """
        logger.debug("IngestMeasurements: device_id=%s, batch_size=%d", command.device_id, len(command.measurements))

        device = await self.device_repository.get_by_id(command.device_id)
        if device is None:
            raise DeviceNotFoundError(
                f"Device with id {command.device_id!r} not found."
            )

        if not device.is_active:
            raise InactiveDeviceError(
                f"Device {command.device_id!r} is inactive. "
                "Measurements cannot be ingested for inactive devices."
            )

        domain_measurements = [
            Measurement(
                id=MeasurementId(item.measurement_id),
                device_id=DeviceId(command.device_id),
                type=MeasurementType(item.type),
                value=MeasurementValue(item.value),
                unit=MeasurementUnit(item.unit),
                timestamp=Timestamp(item.timestamp),
            )
            for item in command.measurements
        ]

        return await self.measurement_repository.save_batch(domain_measurements)
