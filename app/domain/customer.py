from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.value_objects import (
    Country,
    Timestamp,
    CustomerId,
    Email,
    Language,
    Name,
    TimeZone,
)


@dataclass
class Customer:
    """Domain entity representing a Customer composed strictly of Value Objects."""

    name: Name
    email: Email
    id: CustomerId = field(default_factory=CustomerId)
    language: Language | None = None
    country: Country | None = None
    timezone: TimeZone | None = None
    created_at: Timestamp = field(default_factory=Timestamp)
