from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.value_objects import (
    CreatedAt,
    CustomerCountry,
    CustomerEmail,
    CustomerId,
    CustomerLanguage,
    CustomerName,
    CustomerTimeZone,
)


@dataclass
class Customer:
    """Domain entity representing a Customer whose members are Value Objects."""

    name: CustomerName
    email: CustomerEmail
    id: CustomerId = field(default_factory=CustomerId)
    language: CustomerLanguage | None = None
    country: CustomerCountry | None = None
    timezone: CustomerTimeZone | None = None
    created_at: CreatedAt = field(default_factory=CreatedAt)

    def __post_init__(self) -> None:
        if isinstance(self.name, str):
            self.name = CustomerName(self.name)
        if isinstance(self.email, str):
            self.email = CustomerEmail(self.email)
        if isinstance(self.id, (str, UUID)):
            self.id = CustomerId(self.id)
        if isinstance(self.language, str):
            self.language = CustomerLanguage(self.language)
        if isinstance(self.country, str):
            self.country = CustomerCountry(self.country)
        if isinstance(self.timezone, str):
            self.timezone = CustomerTimeZone(self.timezone)
        if isinstance(self.created_at, datetime):
            self.created_at = CreatedAt(self.created_at)
