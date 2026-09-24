from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.device import DeviceModel
from app.infrastructure.db.session import AsyncSessionFactory
from app.main import app

BASE_URL = "http://test"


async def _seed_device(*, is_active: bool = True) -> dict:
    """Insert a customer and a device directly into the DB and return their ids."""
    customer_id = uuid4()
    device_id = uuid4()
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await session.execute(
                insert(CustomerModel).values(
                    id=customer_id,
                    name="Test Customer",
                    email=f"customer-{customer_id}@test.com",
                    created_at=__import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ),
                )
            )
            await session.execute(
                insert(DeviceModel).values(
                    id=device_id,
                    serial_number=f"SN-{device_id}",
                    customer_id=customer_id,
                    status="OFFLINE",
                    is_active=is_active,
                    created_at=__import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ),
                    updated_at=__import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ),
                )
            )
    return {"customer_id": customer_id, "device_id": device_id}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_activate_device_returns_204() -> None:
    ids = await _seed_device(is_active=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{ids['device_id']}/activation",
            json={"is_active": True},
        )
    assert response.status_code == 204


async def test_deactivate_device_returns_204() -> None:
    ids = await _seed_device(is_active=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{ids['device_id']}/activation",
            json={"is_active": False},
        )
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# Idempotent no-op
# ---------------------------------------------------------------------------


async def test_idempotent_activation_returns_204() -> None:
    ids = await _seed_device(is_active=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{ids['device_id']}/activation",
            json={"is_active": True},
        )
    assert response.status_code == 204


async def test_idempotent_deactivation_returns_204() -> None:
    ids = await _seed_device(is_active=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{ids['device_id']}/activation",
            json={"is_active": False},
        )
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# Not found & Validation errors
# ---------------------------------------------------------------------------


async def test_update_activation_nonexistent_device_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{uuid4()}/activation",
            json={"is_active": True},
        )
    assert response.status_code == 404


async def test_update_activation_invalid_payload_returns_422() -> None:
    """
    Semantic / schema validation error:
    The payload is valid JSON syntax, but fails schema validation (missing required field 'is_active').
    FastAPI returns 422 Unprocessable Entity.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.patch(
            f"/devices/{uuid4()}/activation",
            json={"invalid_key": "not_a_bool"},
        )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Dependency Injection override test
# ---------------------------------------------------------------------------


async def test_update_activation_with_dependency_override() -> None:
    """Demonstrates swapping the handler dependency with a mock via app.dependency_overrides."""
    from unittest.mock import AsyncMock
    from app.api.dependencies import get_update_device_activation_handler

    mock_handler = AsyncMock()
    app.dependency_overrides[get_update_device_activation_handler] = lambda: mock_handler
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
            response = await ac.patch(
                f"/devices/{uuid4()}/activation",
                json={"is_active": True},
            )
        assert response.status_code == 204
        mock_handler.handle.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()
