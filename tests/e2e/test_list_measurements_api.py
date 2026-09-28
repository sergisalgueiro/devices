from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert
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


async def _seed_measurement(
    session: AsyncSession,
    device_id,
    *,
    type: str = "temperature",
    value: float = 22.5,
    unit: str = "°C",
    timestamp: datetime | None = None,
) -> dict:
    measurement_id = uuid4()
    ts = timestamp or datetime.now(timezone.utc)
    await session.execute(
        insert(MeasurementModel).values(
            id=measurement_id,
            device_id=device_id,
            type=type,
            value=value,
            unit=unit,
            timestamp=ts,
        )
    )
    return {"measurement_id": measurement_id, "timestamp": ts}


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


async def test_list_measurements_nonexistent_device_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/devices/{uuid4()}/measurements")
    assert response.status_code == 404


async def test_invalid_sort_dir_returns_422(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{ids['device_id']}/measurements",
            params={"sort_dir": "invalid"},
        )
    assert response.status_code == 422


async def test_limit_out_of_range_returns_422(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{ids['device_id']}/measurements",
            params={"limit": 0},
        )
    assert response.status_code == 422

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{ids['device_id']}/measurements",
            params={"limit": 101},
        )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


async def test_list_measurements_empty_device_returns_200(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/devices/{ids['device_id']}/measurements")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None


async def test_list_measurements_returns_device_measurements(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    await _seed_measurement(db_session, device_id)
    await _seed_measurement(db_session, device_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/devices/{device_id}/measurements")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert item["device_id"] == str(device_id)


async def test_list_measurements_filters_by_type(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    await _seed_measurement(db_session, device_id, type="temperature")
    await _seed_measurement(db_session, device_id, type="humidity")

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{device_id}/measurements",
            params={"type": "temperature"},
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["type"] == "temperature"


async def test_list_measurements_filters_by_time_range(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    base = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
    await _seed_measurement(db_session, device_id, timestamp=base - timedelta(hours=1))
    await _seed_measurement(db_session, device_id, timestamp=base)
    await _seed_measurement(db_session, device_id, timestamp=base + timedelta(hours=1))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{device_id}/measurements",
            params={
                "start_time": base.isoformat(),
                "end_time": (base + timedelta(hours=1)).isoformat(),
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1


async def test_list_measurements_default_sort_is_descending(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    base = datetime(2026, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        await _seed_measurement(db_session, device_id, timestamp=base + timedelta(hours=i))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/devices/{device_id}/measurements")
    assert response.status_code == 200
    timestamps = [item["timestamp"] for item in response.json()["items"]]
    assert timestamps == sorted(timestamps, reverse=True)


async def test_list_measurements_cursor_pagination(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    base = datetime(2026, 1, 20, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        await _seed_measurement(db_session, device_id, timestamp=base + timedelta(hours=i))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        page1 = await ac.get(
            f"/devices/{device_id}/measurements",
            params={"limit": 3, "sort_dir": "asc"},
        )
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["items"]) == 3
    assert body1["has_more"] is True
    assert body1["next_cursor"] is not None

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        page2 = await ac.get(
            f"/devices/{device_id}/measurements",
            params={"limit": 3, "sort_dir": "asc", "cursor": body1["next_cursor"]},
        )
    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2["items"]) == 2
    assert body2["has_more"] is False

    ids1 = {item["id"] for item in body1["items"]}
    ids2 = {item["id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


async def test_list_measurements_cursor_with_conflicting_sort_returns_422(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    base = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(3):
        await _seed_measurement(db_session, device_id, timestamp=base + timedelta(hours=i))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        first = await ac.get(
            f"/devices/{device_id}/measurements",
            params={"limit": 2, "sort_dir": "desc"},
        )
    assert first.status_code == 200
    cursor = first.json()["next_cursor"]
    assert cursor is not None

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        conflicting = await ac.get(
            f"/devices/{device_id}/measurements",
            params={"limit": 2, "sort_dir": "asc", "cursor": cursor},
        )
    assert conflicting.status_code == 422


async def test_list_measurements_combined_filters_use_and_logic(db_session: AsyncSession) -> None:
    ids = await _seed_device(db_session)
    device_id = ids["device_id"]
    base = datetime(2026, 1, 25, 12, 0, 0, tzinfo=timezone.utc)
    await _seed_measurement(db_session, device_id, type="temperature", timestamp=base)
    await _seed_measurement(db_session, device_id, type="humidity", timestamp=base)
    await _seed_measurement(db_session, device_id, type="temperature", timestamp=base + timedelta(hours=2))

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(
            f"/devices/{device_id}/measurements",
            params={
                "type": "temperature",
                "end_time": (base + timedelta(hours=1)).isoformat(),
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["type"] == "temperature"
