from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.domain.customer import Customer
from app.domain.exceptions import CustomerNotFoundError
from app.domain.repositories import CustomerRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetCustomerQuery:
    """Query DTO for retrieving a customer by ID."""

    customer_id: UUID


@dataclass
class GetCustomerHandler:
    """Application handler for the GetCustomerQuery use case."""

    customer_repository: CustomerRepository

    async def handle(self, query: GetCustomerQuery) -> Customer:
        """
        Retrieve a customer by ID.

        Raises:
            CustomerNotFoundError: if no customer exists with that id.
        """
        logger.debug("GetCustomer: customer_id=%s", query.customer_id)

        customer = await self.customer_repository.get_by_id(query.customer_id)
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with id {query.customer_id!r} not found."
            )

        return customer
