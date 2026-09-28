from __future__ import annotations

from unittest.mock import AsyncMock

from app.application.customer.list_customers import ListCustomersHandler, ListCustomersQuery
from app.domain.repositories import CustomerListFilters, PaginatedResult
from app.domain.value_objects import Country, Language


class TestListCustomersHandler:
    async def test_delegates_to_repository_with_correct_filters(self) -> None:
        expected = PaginatedResult(items=[], next_cursor=None, has_more=False)
        repo = AsyncMock()
        repo.list.return_value = expected

        handler = ListCustomersHandler(customer_repository=repo)
        result = await handler.handle(
            ListCustomersQuery(country="ES", language="en", limit=10)
        )

        assert result is expected
        repo.list.assert_awaited_once_with(
            filters=CustomerListFilters(country=Country("ES"), language=Language("en")),
            sort_field="created_at",
            sort_direction="asc",
            limit=10,
            cursor=None,
        )

    async def test_passes_cursor_and_sort_params(self) -> None:
        repo = AsyncMock()
        repo.list.return_value = PaginatedResult(items=[], next_cursor=None, has_more=False)

        handler = ListCustomersHandler(customer_repository=repo)
        await handler.handle(
            ListCustomersQuery(
                sort_field="name",
                sort_direction="desc",
                limit=5,
                cursor="some-cursor",
            )
        )

        repo.list.assert_awaited_once_with(
            filters=CustomerListFilters(),
            sort_field="name",
            sort_direction="desc",
            limit=5,
            cursor="some-cursor",
        )

    async def test_returns_paginated_result_with_has_more(self) -> None:
        from app.domain.customer import Customer
        from app.domain.value_objects import CustomerId, Email, Name

        customers = [
            Customer(id=CustomerId(), name=Name(f"User {i}"), email=Email(f"user{i}@example.com"))
            for i in range(3)
        ]
        expected = PaginatedResult(items=customers, next_cursor="cursor-token", has_more=True)
        repo = AsyncMock()
        repo.list.return_value = expected

        handler = ListCustomersHandler(customer_repository=repo)
        result = await handler.handle(ListCustomersQuery(limit=3))

        assert result.has_more is True
        assert result.next_cursor == "cursor-token"
        assert len(result.items) == 3
