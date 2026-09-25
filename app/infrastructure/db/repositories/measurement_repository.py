from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.measurement import Measurement
from app.domain.repositories import MeasurementListFilters, MeasurementRepository, PaginatedResult
from app.domain.value_objects import DeviceId, MeasurementId, MeasurementType, MeasurementUnit, MeasurementValue, Timestamp
from app.infrastructure.db.models.measurement import MeasurementModel

logger = logging.getLogger(__name__)


def _encode_cursor(sort_direction: str, timestamp: datetime, row_id: UUID) -> str:
    payload = {"f": "timestamp", "d": sort_direction, "v": timestamp.isoformat(), "id": str(row_id)}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    return encoded.rstrip("=")


def _decode_cursor(cursor: str) -> tuple[str, datetime, UUID]:
    padded = cursor + "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded).decode())
    sort_direction: str = payload["d"]
    cursor_timestamp = datetime.fromisoformat(payload["v"])
    cursor_id = UUID(payload["id"])
    return sort_direction, cursor_timestamp, cursor_id


class SqlAlchemyMeasurementRepository(MeasurementRepository):
    """SQLAlchemy implementation of the MeasurementRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, measurement: Measurement) -> None:
        """Persist a single Measurement."""
        logger.debug("INSERT measurement: id=%s, device_id=%s", measurement.id.value, measurement.device_id.value)
        row = MeasurementModel(
            id=measurement.id.value,
            device_id=measurement.device_id.value,
            type=measurement.type.value,
            value=measurement.value.value,
            unit=measurement.unit.value,
            timestamp=measurement.timestamp.value,
        )
        self._session.add(row)
        await self._session.flush()
        logger.debug("Measurement flushed: id=%s", measurement.id.value)

    async def save_batch(self, measurements: list[Measurement]) -> int:
        """Persist a batch of measurements, skipping duplicates by id.

        Uses PostgreSQL INSERT ... ON CONFLICT (id) DO NOTHING for
        atomic, idempotent upsert behaviour.

        Returns the number of newly inserted measurements.
        """
        if not measurements:
            return 0

        logger.debug("Batch INSERT measurements: count=%d", len(measurements))

        values = [
            {
                "id": m.id.value,
                "device_id": m.device_id.value,
                "type": m.type.value,
                "value": m.value.value,
                "unit": m.unit.value,
                "timestamp": m.timestamp.value,
            }
            for m in measurements
        ]

        stmt = pg_insert(MeasurementModel).values(values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        result = await self._session.execute(stmt)
        await self._session.flush()
        new_count = result.rowcount
        logger.debug(
            "Batch INSERT result: submitted=%d, inserted=%d, duplicates=%d",
            len(measurements), new_count, len(measurements) - new_count,
        )
        return new_count

    async def list(
        self,
        device_id: UUID,
        filters: MeasurementListFilters,
        sort_field: str,
        sort_direction: str,
        limit: int,
        cursor: str | None,
    ) -> PaginatedResult[Measurement]:
        logger.debug(
            "LIST measurements: device_id=%s, sort=%s/%s, limit=%d, cursor=%s",
            device_id, sort_field, sort_direction, limit, cursor,
        )

        cursor_timestamp: datetime | None = None
        cursor_id: UUID | None = None
        if cursor is not None:
            sort_direction, cursor_timestamp, cursor_id = _decode_cursor(cursor)

        stmt = select(MeasurementModel).where(MeasurementModel.device_id == device_id)

        if filters.type is not None:
            stmt = stmt.where(MeasurementModel.type == filters.type)
        if filters.start_time is not None:
            stmt = stmt.where(MeasurementModel.timestamp >= filters.start_time)
        if filters.end_time is not None:
            stmt = stmt.where(MeasurementModel.timestamp < filters.end_time)

        if cursor_timestamp is not None and cursor_id is not None:
            col = MeasurementModel.timestamp
            if sort_direction == "asc":
                stmt = stmt.where(
                    or_(col > cursor_timestamp, and_(col == cursor_timestamp, MeasurementModel.id > cursor_id))
                )
            else:
                stmt = stmt.where(
                    or_(col < cursor_timestamp, and_(col == cursor_timestamp, MeasurementModel.id < cursor_id))
                )

        if sort_direction == "asc":
            stmt = stmt.order_by(MeasurementModel.timestamp.asc(), MeasurementModel.id.asc())
        else:
            stmt = stmt.order_by(MeasurementModel.timestamp.desc(), MeasurementModel.id.desc())

        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor: str | None = None
        if has_more and items:
            last = items[-1]
            next_cursor = _encode_cursor(sort_direction, last.timestamp, last.id)

        return PaginatedResult(
            items=[self._to_domain(row) for row in items],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _to_domain(row: MeasurementModel) -> Measurement:
        return Measurement(
            id=MeasurementId(row.id),
            device_id=DeviceId(row.device_id),
            type=MeasurementType(row.type),
            value=MeasurementValue(row.value),
            unit=MeasurementUnit(row.unit),
            timestamp=Timestamp(row.timestamp),
        )
