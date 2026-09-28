from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.customer.get_customer import GetCustomerHandler, GetCustomerQuery
from app.domain.customer import Customer
from app.domain.exceptions import CustomerNotFoundError
from app.domain.value_objects import CustomerId, Email, Name


def _make_customer() -> Customer:
    return Customer(
        id=CustomerId(uuid4()),
        name=Name("Test User"),
        email=Email("test@example.com"),
    )


class TestGetCustomerHandler:
    async def test_returns_customer_when_found(self) -> None:
        customer = _make_customer()
        repo = AsyncMock()
        repo.get_by_id.return_value = customer

        handler = GetCustomerHandler(customer_repository=repo)
        result = await handler.handle(GetCustomerQuery(customer_id=customer.id.value))

        assert result is customer
        repo.get_by_id.assert_awaited_once_with(customer.id)

    async def test_raises_when_customer_not_found(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = None

        handler = GetCustomerHandler(customer_repository=repo)
        with pytest.raises(CustomerNotFoundError):
            await handler.handle(GetCustomerQuery(customer_id=uuid4()))
