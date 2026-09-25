from __future__ import annotations

from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app

BASE_URL = "http://test"


async def test_create_device_returns_201() -> None:
    serial = f"SN-{uuid4()}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/devices", json={"serial_number": serial})

    assert response.status_code == 201
    body = response.json()
    assert body["serial_number"] == serial
    assert body["customer_id"] is None
    assert body["timezone"] is None
    assert body["is_active"] is True
    assert "id" in body
    assert "status" in body
    assert "created_at" in body
    assert "updated_at" in body


async def test_create_device_duplicate_serial_number_returns_409() -> None:
    serial = f"SN-{uuid4()}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        first = await ac.post("/devices", json={"serial_number": serial})
    assert first.status_code == 201

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        second = await ac.post("/devices", json={"serial_number": serial})
    assert second.status_code == 409


async def test_create_device_empty_serial_number_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/devices", json={"serial_number": ""})
    assert response.status_code == 422


async def test_create_device_missing_serial_number_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/devices", json={})
    assert response.status_code == 422
