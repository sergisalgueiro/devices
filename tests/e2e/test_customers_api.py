from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.session import AsyncSessionFactory
from app.main import app

BASE_URL = "http://test"


async def _seed_customer(
    *,
    name: str = "Test Customer",
    email: str | None = None,
    country: str | None = None,
    language: str | None = None,
) -> dict:
    customer_id = uuid4()
    email = email or f"customer-{customer_id}@test.com"
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await session.execute(
                insert(CustomerModel).values(
                    id=customer_id,
                    name=name,
                    email=email,
                    country=country,
                    language=language,
                    created_at=datetime.now(timezone.utc),
                )
            )
    return {"customer_id": customer_id, "email": email}


# ---------------------------------------------------------------------------
# Create customer
# ---------------------------------------------------------------------------


async def test_create_customer_returns_201() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/customers",
            json={"name": "Alice Smith", "email": "alice.smith@example.com"},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice.smith@example.com"
    assert body["name"] == "Alice Smith"
    assert "id" in body
    assert "created_at" in body


async def test_create_customer_with_optional_fields_returns_201() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/customers",
            json={
                "name": "Bob Jones",
                "email": f"bob.{uuid4()}@example.com",
                "language": "en",
                "country": "US",
                "timezone": "America/New_York",
            },
        )
    assert response.status_code == 201
    body = response.json()
    assert body["language"] == "en"
    assert body["country"] == "US"


async def test_create_customer_duplicate_email_returns_409() -> None:
    seeded = await _seed_customer(email="duplicate@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/customers",
            json={"name": "Second Alice", "email": seeded["email"]},
        )
    assert response.status_code == 409


async def test_create_customer_invalid_email_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/customers",
            json={"name": "Bad Email", "email": "not-an-email"},
        )
    assert response.status_code == 422


async def test_create_customer_empty_name_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post(
            "/customers",
            json={"name": "", "email": "valid@example.com"},
        )
    assert response.status_code == 422


async def test_create_customer_missing_required_fields_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.post("/customers", json={"name": "No Email"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Get customer by ID
# ---------------------------------------------------------------------------


async def test_get_customer_returns_200() -> None:
    seeded = await _seed_customer(name="Jane Doe", email=f"jane.{uuid4()}@example.com")
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/customers/{seeded['customer_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(seeded["customer_id"])
    assert body["email"] == seeded["email"]


async def test_get_customer_nonexistent_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get(f"/customers/{uuid4()}")
    assert response.status_code == 404


async def test_get_customer_invalid_uuid_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers/not-a-uuid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List customers
# ---------------------------------------------------------------------------


async def test_list_customers_returns_200_with_empty_list() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers", params={"email": f"nobody-{uuid4()}@example.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None


async def test_list_customers_returns_seeded_customer() -> None:
    unique_email = f"list-test-{uuid4()}@example.com"
    await _seed_customer(email=unique_email)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers", params={"email": unique_email})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["email"] == unique_email


async def test_list_customers_filters_by_country() -> None:
    unique_country = "DE"
    suffix = str(uuid4())[:8]
    await _seed_customer(email=f"de-user-{suffix}@example.com", country=unique_country)
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers", params={"country": unique_country, "email": f"de-user-{suffix}@example.com"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 1
    assert all(item["country"] == unique_country for item in body["items"])


async def test_list_customers_pagination_cursor_works() -> None:
    suffix = str(uuid4())[:8]
    emails = [f"page-{suffix}-{i}@example.com" for i in range(3)]
    for email in emails:
        await _seed_customer(email=email, name=f"Page User {suffix}")

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        first_response = await ac.get(
            "/customers",
            params={"name": f"Page User {suffix}", "limit": 2, "sort_by": "created_at", "sort_dir": "asc"},
        )
    assert first_response.status_code == 200
    first_body = first_response.json()
    assert len(first_body["items"]) == 2
    assert first_body["has_more"] is True
    assert first_body["next_cursor"] is not None

    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        second_response = await ac.get(
            "/customers",
            params={
                "name": f"Page User {suffix}",
                "limit": 2,
                "sort_by": "created_at",
                "sort_dir": "asc",
                "cursor": first_body["next_cursor"],
            },
        )
    assert second_response.status_code == 200
    second_body = second_response.json()
    assert len(second_body["items"]) == 1
    assert second_body["has_more"] is False

    first_ids = {item["id"] for item in first_body["items"]}
    second_ids = {item["id"] for item in second_body["items"]}
    assert first_ids.isdisjoint(second_ids)


async def test_list_customers_invalid_sort_by_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers", params={"sort_by": "invalid_field"})
    assert response.status_code == 422


async def test_list_customers_limit_out_of_range_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        response = await ac.get("/customers", params={"limit": 200})
    assert response.status_code == 422
