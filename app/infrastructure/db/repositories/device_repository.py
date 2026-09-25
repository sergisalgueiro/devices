from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.device import Device
from app.domain.repositories import DeviceRepository
from app.domain.value_objects import (
    CreatedAt,
    CustomerId,
    DeviceId,
    DeviceStatus,
    SerialNumber,
    TimeZone,
    UpdatedAt,
)
from app.infrastructure.db.models.device import DeviceModel

logger = logging.getLogger(__name__)


class SqlAlchemyDeviceRepository(DeviceRepository):
    """SQLAlchemy implementation of the DeviceRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, device_id: UUID) -> Device | None:
        """Return the Device with the given id, or None if not found."""
        logger.debug("SELECT device: id=%s", device_id)
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.id == device_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            logger.debug("Device not found in DB: id=%s", device_id)
            return None
        logger.debug("Device found: id=%s", device_id)
        return self._to_domain(row)

    async def get_by_serial_number(self, serial_number: str) -> Device | None:
        """Return the Device with the given serial number, or None if not found."""
        logger.debug("SELECT device: serial_number=%s", serial_number)
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.serial_number == serial_number)
        )
        row = result.scalar_one_or_none()
        if row is None:
            logger.debug("Device not found in DB: serial_number=%s", serial_number)
            return None
        logger.debug("Device found: serial_number=%s", serial_number)
        return self._to_domain(row)

    async def save(self, device: Device) -> None:
        """Persist a new or updated Device."""
        result = await self._session.execute(
            select(DeviceModel).where(DeviceModel.id == device.id.value)
        )
        row = result.scalar_one_or_none()

        if row is None:
            logger.debug("INSERT device: id=%s", device.id.value)
            row = DeviceModel(id=device.id.value)
            self._session.add(row)
        else:
            logger.debug("UPDATE device: id=%s", device.id.value)

        row.serial_number = device.serial_number.value
        row.customer_id = device.customer_id.value
        row.status = device.status.value
        row.is_active = device.is_active
        row.timezone = device.timezone.value if device.timezone is not None else None
        row.created_at = device.created_at.value
        row.updated_at = device.updated_at.value

        await self._session.flush()
        logger.debug("Device flushed: id=%s", device.id.value)

    @staticmethod
    def _to_domain(row: DeviceModel) -> Device:
        """Reconstitute a Device domain entity from a DeviceModel ORM row."""
        return Device(
            id=DeviceId(row.id),
            serial_number=SerialNumber(row.serial_number),
            customer_id=CustomerId(row.customer_id),
            status=DeviceStatus(row.status),
            is_active=row.is_active,
            timezone=TimeZone(row.timezone) if row.timezone is not None else None,
            created_at=CreatedAt(row.created_at),
            updated_at=UpdatedAt(row.updated_at),
        )
