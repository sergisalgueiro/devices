from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.measurement import Measurement
from app.domain.repositories import MeasurementRepository
from app.infrastructure.db.models.measurement import MeasurementModel


class SqlAlchemyMeasurementRepository(MeasurementRepository):
    """SQLAlchemy implementation of the MeasurementRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, measurement: Measurement) -> None:
        """Persist a single Measurement."""
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

    async def save_batch(self, measurements: list[Measurement]) -> int:
        """Persist a batch of measurements, skipping duplicates by id.

        Uses PostgreSQL INSERT ... ON CONFLICT (id) DO NOTHING for
        atomic, idempotent upsert behaviour.

        Returns the number of newly inserted measurements.
        """
        if not measurements:
            return 0

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
        return result.rowcount
