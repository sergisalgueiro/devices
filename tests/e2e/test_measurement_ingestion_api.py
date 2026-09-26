from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.device import DeviceModel
from app.infrastructure.db.models.measurement import MeasurementModel
from app.main import app

BASE_URL = "http://test"


async def _seed_device(session: AsyncSession, *, is_active: bool = True) -> dict:
    customer_id = uuid4()
    device_id = uuid4()
    now = datetime.now(timezone.utc)
    await session.execute(
        insert(CustomerModel).values(
            id=customer_id,
            name="Test Customer",
            email=f"customer-{customer_id}@test.com",
            created_at=now,
        )
    )
    await session.execute(
        insert(DeviceModel).values(
            id=device_id,
            serial_number=f"SN-{device_id}",
            customer_id=customer_id,
            status="OFFLINE",
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    )
    return {"customer_id": customer_id, "device_id": device_id}


def _measurement_payload(*, measurement_id: str | None = None) -> dict:
    return {
        "measurement_id": measurement_id or str(uuid4()),
        "type": "temperature",
        "value": 22.5,
        "unit": "°C",
        "timestamp": "2026-09-25T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_ingest_single_measurement_returns_201(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session, is_active=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[_measurement_payload()],
        )
    assert response.status_code == 201


async def test_ingest_batch_returns_201(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session, is_active=True)
    payload = [_measurement_payload() for _ in range(5)]
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=payload,
        )
    assert response.status_code == 201


async def test_duplicate_measurement_is_idempotent(db_session: AsyncSession) -> None:
    """Sending the same measurement_id twice must succeed and create only one DB row."""
    ids = await _seed_device(db_session, is_active=True)
    measurement_id = str(uuid4())
    item = _measurement_payload(measurement_id=measurement_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        first = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[item],
        )
        second = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[item],
        )

    assert first.status_code == 201
    assert second.status_code == 201

    # Verify only one row exists in the DB for this measurement_id
    import uuid
    result = await db_session.execute(
        select(MeasurementModel).where(
            MeasurementModel.id == uuid.UUID(measurement_id)
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


async def test_ingest_nonexistent_device_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{uuid4()}/measurements",
            json=[_measurement_payload()],
        )
    assert response.status_code == 404


async def test_ingest_inactive_device_returns_422(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session, is_active=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[_measurement_payload()],
        )
    assert response.status_code == 422


async def test_ingest_invalid_payload_returns_422(db_session: AsyncSession) -> None:
    """Malformed measurement object (missing required fields) → 422."""
    ids = await _seed_device(db_session, is_active=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[{"not_a_valid_field": True}],
        )
    assert response.status_code == 422


async def test_ingest_empty_array_returns_422(db_session: AsyncSession) -> None:
    """Empty array violates min_length=1 constraint → 422."""
    ids = await _seed_device(db_session, is_active=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=[],
        )
    assert response.status_code == 422


async def test_ingest_oversized_batch_returns_422(db_session: AsyncSession) -> None:
    """Array with >1,000 items violates max_length=1000 constraint → 422."""
    ids = await _seed_device(db_session, is_active=True)
    payload = [_measurement_payload() for _ in range(1001)]
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            f"/devices/{ids['device_id']}/measurements",
            json=payload,
        )
    assert response.status_code == 422
