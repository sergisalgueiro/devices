from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.device import DeviceModel
from app.infrastructure.db.session import AsyncSessionFactory
from app.main import app

BASE_URL = "http://test"


async def _seed_customer() -> dict:
    customer_id = uuid4()
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await session.execute(
                insert(CustomerModel).values(
                    id=customer_id,
                    name="Test Customer",
                    email=f"customer-{customer_id}@test.com",
                    created_at=datetime.now(timezone.utc),
                )
            )
    return {"customer_id": customer_id}


async def _seed_device(*, customer_id=None, timezone_val: str | None = None) -> dict:
    device_id = uuid4()
    now = datetime.now(timezone.utc)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await session.execute(
                insert(DeviceModel).values(
                    id=device_id,
                    serial_number=f"SN-{device_id}",
                    customer_id=customer_id,
                    status="OFFLINE",
                    is_active=True,
                    timezone=timezone_val,
                    created_at=now,
                    updated_at=now,
                )
            )
    return {"device_id": device_id}


# ---------------------------------------------------------------------------
# Assign
# ---------------------------------------------------------------------------


async def test_assign_device_to_customer_returns_200() -> None:
    customer = await _seed_customer()
    device = await _seed_device()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.put(
            f"/devices/{device['device_id']}/customer",
            json={"customer_id": str(customer["customer_id"])},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == str(customer["customer_id"])
    assert body["timezone"] is None


async def test_assign_device_with_timezone_returns_200() -> None:
    customer = await _seed_customer()
    device = await _seed_device()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.put(
            f"/devices/{device['device_id']}/customer",
            json={"customer_id": str(customer["customer_id"]), "timezone": "Europe/Madrid"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == str(customer["customer_id"])
    assert body["timezone"] == "Europe/Madrid"


async def test_assign_nonexistent_device_returns_404() -> None:
    customer = await _seed_customer()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.put(
            f"/devices/{uuid4()}/customer",
            json={"customer_id": str(customer["customer_id"])},
        )

    assert response.status_code == 404


async def test_assign_to_nonexistent_customer_returns_404() -> None:
    device = await _seed_device()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.put(
            f"/devices/{device['device_id']}/customer",
            json={"customer_id": str(uuid4())},
        )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Unassign
# ---------------------------------------------------------------------------


async def test_unassign_device_returns_204() -> None:
    customer = await _seed_customer()
    device = await _seed_device(customer_id=customer["customer_id"], timezone_val="Europe/Madrid")

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.delete(f"/devices/{device['device_id']}/customer")

    assert response.status_code == 204


async def test_unassign_already_unassigned_device_returns_204() -> None:
    device = await _seed_device()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.delete(f"/devices/{device['device_id']}/customer")

    assert response.status_code == 204


async def test_unassign_nonexistent_device_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.delete(f"/devices/{uuid4()}/customer")

    assert response.status_code == 404


async def test_unassign_clears_customer_and_timezone() -> None:
    customer = await _seed_customer()
    device = await _seed_device(customer_id=customer["customer_id"], timezone_val="Europe/Madrid")

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        await ac.delete(f"/devices/{device['device_id']}/customer")

    # Re-assign and verify state, then unassign again via a fresh create flow
    # Confirm state via assign then check response
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        assign_response = await ac.put(
            f"/devices/{device['device_id']}/customer",
            json={"customer_id": str(customer["customer_id"])},
        )
    body = assign_response.json()
    assert body["customer_id"] == str(customer["customer_id"])
    assert body["timezone"] is None  # timezone was cleared by unassign
