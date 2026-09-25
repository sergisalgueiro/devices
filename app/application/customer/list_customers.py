from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.customer import Customer
from app.domain.repositories import CustomerListFilters, CustomerRepository, PaginatedResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListCustomersQuery:
    """Query DTO for listing customers with filters and cursor-based pagination."""

    sort_field: str = "created_at"
    sort_direction: str = "asc"
    limit: int = 20
    cursor: str | None = None
    email: str | None = None
    country: str | None = None
    language: str | None = None
    name: str | None = None


@dataclass
class ListCustomersHandler:
    """Application handler for the ListCustomersQuery use case."""

    customer_repository: CustomerRepository

    async def handle(self, query: ListCustomersQuery) -> PaginatedResult[Customer]:
        """Return a paginated, optionally filtered list of customers."""
        logger.debug(
            "ListCustomers: sort=%s/%s, limit=%d, cursor=%s",
            query.sort_field, query.sort_direction, query.limit, query.cursor,
        )

        filters = CustomerListFilters(
            email=query.email,
            country=query.country,
            language=query.language,
            name=query.name,
        )

        return await self.customer_repository.list(
            filters=filters,
            sort_field=query.sort_field,
            sort_direction=query.sort_direction,
            limit=query.limit,
            cursor=query.cursor,
        )
