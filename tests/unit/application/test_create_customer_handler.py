from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.customer.create_customer import CreateCustomerCommand, CreateCustomerHandler
from app.domain.customer import Customer
from app.domain.exceptions import CustomerEmailAlreadyExistsError, DomainValidationError
from app.domain.value_objects import CustomerId, Email, Name


def _make_customer(email: str = "existing@example.com") -> Customer:
    return Customer(
        id=CustomerId(),
        name=Name("Existing User"),
        email=Email(email),
    )


class TestCreateCustomerHandler:
    async def test_creates_customer_and_returns_it(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        customer = await handler.handle(
            CreateCustomerCommand(name="Alice", email="alice@example.com")
        )

        assert customer.name.value == "Alice"
        assert customer.email.value == "alice@example.com"
        repo.save.assert_awaited_once_with(customer)

    async def test_creates_customer_with_optional_fields(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        customer = await handler.handle(
            CreateCustomerCommand(
                name="Bob",
                email="bob@example.com",
                language="en",
                country="US",
                timezone="America/New_York",
            )
        )

        assert customer.language is not None
        assert customer.language.value == "en"
        assert customer.country is not None
        assert customer.country.value == "US"
        assert customer.timezone is not None

    async def test_raises_when_email_already_exists(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = _make_customer("alice@example.com")

        handler = CreateCustomerHandler(customer_repository=repo)
        with pytest.raises(CustomerEmailAlreadyExistsError):
            await handler.handle(
                CreateCustomerCommand(name="Alice", email="alice@example.com")
            )

        repo.save.assert_not_awaited()

    async def test_raises_on_invalid_email(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        with pytest.raises(DomainValidationError):
            await handler.handle(
                CreateCustomerCommand(name="Alice", email="not-an-email")
            )

        repo.save.assert_not_awaited()

    async def test_raises_on_empty_name(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        with pytest.raises(DomainValidationError):
            await handler.handle(
                CreateCustomerCommand(name="", email="alice@example.com")
            )

        repo.save.assert_not_awaited()

    async def test_trims_whitespace_from_name(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        customer = await handler.handle(
            CreateCustomerCommand(name="  Alice  ", email="alice@example.com")
        )

        assert customer.name.value == "Alice"

    async def test_trims_whitespace_from_email(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        customer = await handler.handle(
            CreateCustomerCommand(name="Alice", email="  alice@example.com  ")
        )

        assert customer.email.value == "alice@example.com"

    async def test_raises_on_invalid_country(self) -> None:
        repo = AsyncMock()
        repo.get_by_email.return_value = None

        handler = CreateCustomerHandler(customer_repository=repo)
        with pytest.raises(DomainValidationError):
            await handler.handle(
                CreateCustomerCommand(name="Alice", email="alice@example.com", country="INVALID")
            )

        repo.save.assert_not_awaited()
