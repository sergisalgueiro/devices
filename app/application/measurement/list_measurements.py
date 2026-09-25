from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.exceptions import DeviceNotFoundError
from app.domain.measurement import Measurement
from app.domain.repositories import DeviceRepository, MeasurementListFilters, MeasurementRepository, PaginatedResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListMeasurementsQuery:
    """Query DTO for listing measurements for a device with filters and cursor-based pagination."""

    device_id: UUID
    sort_field: str = "timestamp"
    sort_direction: str = "desc"
    limit: int = 20
    cursor: str | None = None
    type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass
class ListMeasurementsHandler:
    """Application handler for the ListMeasurementsQuery use case."""

    device_repository: DeviceRepository
    measurement_repository: MeasurementRepository

    async def handle(self, query: ListMeasurementsQuery) -> PaginatedResult[Measurement]:
        """Return a paginated, optionally filtered list of measurements for a device.

        Raises:
            DeviceNotFoundError: if the device does not exist.
        """
        logger.debug(
            "ListMeasurements: device_id=%s, sort=%s/%s, limit=%d, cursor=%s",
            query.device_id, query.sort_field, query.sort_direction, query.limit, query.cursor,
        )

        device = await self.device_repository.get_by_id(query.device_id)
        if device is None:
            raise DeviceNotFoundError(f"Device with id {query.device_id!r} not found.")

        filters = MeasurementListFilters(
            type=query.type,
            start_time=query.start_time,
            end_time=query.end_time,
        )

        return await self.measurement_repository.list(
            device_id=query.device_id,
            filters=filters,
            sort_field=query.sort_field,
            sort_direction=query.sort_direction,
            limit=query.limit,
            cursor=query.cursor,
        )
