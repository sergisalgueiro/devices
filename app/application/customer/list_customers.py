from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from app.domain.customer import Customer
from app.domain.repositories import CustomerListFilters, CustomerRepository, PaginatedResult
from app.domain.value_objects import Country, Email, Language, Name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListCustomersQuery:
    """Query DTO for listing customers with filters and cursor-based pagination."""

    sort_field: Literal["created_at", "name", "email"] = "created_at"
    sort_direction: Literal["asc", "desc"] = "asc"
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
            email=Email(query.email) if query.email is not None else None,
            country=Country(query.country) if query.country is not None else None,
            language=Language(query.language) if query.language is not None else None,
            name=Name(query.name) if query.name is not None else None,
        )

        return await self.customer_repository.list(
            filters=filters,
            sort_field=query.sort_field,
            sort_direction=query.sort_direction,
            limit=query.limit,
            cursor=query.cursor,
        )
