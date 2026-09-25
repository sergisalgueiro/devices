from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.infrastructure.db.models.customer import CustomerModel
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


async def test_create_device_returns_201() -> None:
    seeded = await _seed_customer()
    serial = f"SN-{uuid4()}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/devices",
            json={"serial_number": serial, "customer_id": str(seeded["customer_id"])},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["serial_number"] == serial
    assert body["customer_id"] == str(seeded["customer_id"])
    assert body["is_active"] is True
    assert "id" in body
    assert "status" in body
    assert "created_at" in body
    assert "updated_at" in body


async def test_create_device_with_timezone_returns_201() -> None:
    seeded = await _seed_customer()

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/devices",
            json={
                "serial_number": f"SN-{uuid4()}",
                "customer_id": str(seeded["customer_id"]),
                "timezone": "Europe/Madrid",
            },
        )
    assert response.status_code == 201
    assert response.json()["timezone"] == "Europe/Madrid"


async def test_create_device_duplicate_serial_number_returns_409() -> None:
    seeded = await _seed_customer()
    serial = f"SN-{uuid4()}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        first = await ac.post(
            "/devices",
            json={"serial_number": serial, "customer_id": str(seeded["customer_id"])},
        )
    assert first.status_code == 201

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        second = await ac.post(
            "/devices",
            json={"serial_number": serial, "customer_id": str(seeded["customer_id"])},
        )
    assert second.status_code == 409


async def test_create_device_nonexistent_customer_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/devices",
            json={"serial_number": f"SN-{uuid4()}", "customer_id": str(uuid4())},
        )
    assert response.status_code == 404


async def test_create_device_empty_serial_number_returns_422() -> None:
    seeded = await _seed_customer()
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/devices",
            json={"serial_number": "", "customer_id": str(seeded["customer_id"])},
        )
    assert response.status_code == 422


async def test_create_device_missing_required_fields_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/devices", json={"serial_number": f"SN-{uuid4()}"})
    assert response.status_code == 422
