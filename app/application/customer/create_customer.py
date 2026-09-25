from __future__ import annotations

import logging
from dataclasses import dataclass

from app.domain.customer import Customer
from app.domain.exceptions import CustomerEmailAlreadyExistsError
from app.domain.repositories import CustomerRepository
from app.domain.value_objects import Country, Email, Language, Name, TimeZone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateCustomerCommand:
    """Command DTO for creating a new customer."""

    name: str
    email: str
    language: str | None = None
    country: str | None = None
    timezone: str | None = None


@dataclass
class CreateCustomerHandler:
    """Application handler for the CreateCustomerCommand use case."""

    customer_repository: CustomerRepository

    async def handle(self, command: CreateCustomerCommand) -> Customer:
        """
        Create a new customer.

        Raises:
            CustomerEmailAlreadyExistsError: if the email is already registered.
            DomainValidationError: if any field fails domain validation.
        """
        logger.debug("CreateCustomer: email=%s", command.email)

        existing = await self.customer_repository.get_by_email(command.email)
        if existing is not None:
            raise CustomerEmailAlreadyExistsError(
                f"A customer with email {command.email!r} already exists."
            )

        customer = Customer(
            name=Name(command.name),
            email=Email(command.email),
            language=Language(command.language) if command.language is not None else None,
            country=Country(command.country) if command.country is not None else None,
            timezone=TimeZone(command.timezone) if command.timezone is not None else None,
        )

        await self.customer_repository.save(customer)
        logger.info("Customer created: id=%s, email=%s", customer.id.value, command.email)
        return customer
