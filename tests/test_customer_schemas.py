from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate


def test_customer_create_valid():
    data = CustomerCreate(
        name="Alice Smith",
        email="alice@example.com",
        country="ES",
        language="es",
        timezone="Europe/Madrid",
    )
    assert data.name == "Alice Smith"
    assert data.email == "alice@example.com"
    assert data.country == "ES"
    assert data.language == "es"
    assert data.timezone == "Europe/Madrid"


def test_customer_create_optional_none():
    data = CustomerCreate(
        name="Bob Jones",
        email="bob@example.com",
    )
    assert data.country is None
    assert data.language is None
    assert data.timezone is None


def test_customer_create_invalid_country():
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            name="Alice Smith",
            email="alice@example.com",
            country="INVALID_COUNTRY",
        )
    assert "country" in str(exc_info.value)


def test_customer_create_invalid_language():
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            name="Alice Smith",
            email="alice@example.com",
            language="invalid_lang",
        )
    assert "language" in str(exc_info.value)


def test_customer_create_invalid_timezone():
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            name="Alice Smith",
            email="alice@example.com",
            timezone="Mars/Olympus",
        )
    assert "timezone" in str(exc_info.value)


def test_customer_create_invalid_email():
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(
            name="Alice Smith",
            email="not-an-email",
        )
    assert "email" in str(exc_info.value)


def test_customer_response_from_domain_entity():
    customer = Customer(
        id=uuid4(),
        name="Charlie Brown",
        email="charlie@example.com",
        country="US",
        language="en",
        timezone="America/New_York",
        created_at=datetime.now(timezone.utc),
    )
    response = CustomerResponse.model_validate(customer)
    assert response.id == customer.id.value
    assert response.name == customer.name.value
    assert response.email == customer.email.value
    assert response.country == (customer.country.value if customer.country else None)
    assert response.language == (customer.language.value if customer.language else None)
    assert response.timezone == (customer.timezone.value if customer.timezone else None)
    assert response.created_at == customer.created_at.value
