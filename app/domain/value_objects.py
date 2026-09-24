from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Generic, TypeVar
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.exceptions import (
    InvalidCreatedAtError,
    InvalidCustomerCountryError,
    InvalidCustomerEmailError,
    InvalidCustomerIdError,
    InvalidCustomerLanguageError,
    InvalidCustomerNameError,
    InvalidCustomerTimeZoneError,
)

T = TypeVar("T")

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_COUNTRY_REGEX = re.compile(r"^[A-Z]{2}$")
_LANGUAGE_REGEX = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")


@dataclass(frozen=True)
class ValueObject(Generic[T]):
    """Base class for all domain Value Objects."""

    value: T

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class CustomerId(ValueObject[UUID]):
    """Value object representing a customer's unique identifier."""

    value: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if isinstance(self.value, str):
            try:
                object.__setattr__(self, "value", UUID(self.value))
            except (ValueError, TypeError, AttributeError) as exc:
                raise InvalidCustomerIdError(
                    f"Invalid UUID string for CustomerId: {self.value!r}"
                ) from exc
        elif not isinstance(self.value, UUID):
            raise InvalidCustomerIdError(
                f"CustomerId must be a UUID instance or valid UUID string, got {type(self.value).__name__}"
            )


@dataclass(frozen=True)
class CustomerName(ValueObject[str]):
    """Value object representing a customer's name."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCustomerNameError(
                f"CustomerName must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidCustomerNameError("CustomerName cannot be empty or whitespace only")
        if len(self.value) > 255:
            raise InvalidCustomerNameError(
                f"CustomerName cannot exceed 255 characters (got {len(self.value)})"
            )


@dataclass(frozen=True)
class CustomerEmail(ValueObject[str]):
    """Value object representing a customer's email address."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCustomerEmailError(
                f"CustomerEmail must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidCustomerEmailError("CustomerEmail cannot be empty")
        if not _EMAIL_REGEX.match(trimmed):
            raise InvalidCustomerEmailError(f"Invalid email address format: {self.value!r}")


@dataclass(frozen=True)
class CustomerLanguage(ValueObject[str]):
    """Value object representing a customer's preferred language (ISO 639-1 or BCP 47)."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCustomerLanguageError(
                f"CustomerLanguage must be a string, got {type(self.value).__name__}"
            )
        if not _LANGUAGE_REGEX.match(self.value):
            raise InvalidCustomerLanguageError(
                f"CustomerLanguage must be a valid ISO 639-1 or BCP 47 code (e.g. 'en', 'en-US'), got {self.value!r}"
            )


@dataclass(frozen=True)
class CustomerCountry(ValueObject[str]):
    """Value object representing a customer's country code (ISO 3166-1 alpha-2)."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCustomerCountryError(
                f"CustomerCountry must be a string, got {type(self.value).__name__}"
            )
        if not _COUNTRY_REGEX.match(self.value):
            raise InvalidCustomerCountryError(
                f"CustomerCountry must be a 2-letter uppercase ISO 3166-1 alpha-2 code (e.g. 'ES', 'US'), got {self.value!r}"
            )


@dataclass(frozen=True)
class CustomerTimeZone(ValueObject[str]):
    """Value object representing a customer's IANA timezone."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCustomerTimeZoneError(
                f"CustomerTimeZone must be a string, got {type(self.value).__name__}"
            )
        try:
            ZoneInfo(self.value)
        except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
            raise InvalidCustomerTimeZoneError(
                f"CustomerTimeZone must be a valid IANA Time Zone identifier (e.g. 'Europe/Madrid', 'UTC'), got {self.value!r}"
            ) from exc


@dataclass(frozen=True)
class CreatedAt(ValueObject[datetime]):
    """Value object representing an entity creation timestamp in strict timezone-aware UTC."""

    value: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise InvalidCreatedAtError(
                f"CreatedAt must be a datetime instance, got {type(self.value).__name__}"
            )
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise InvalidCreatedAtError("CreatedAt datetime must be timezone-aware (UTC)")
        if self.value.utcoffset() != timezone.utc.utcoffset(None):
            raise InvalidCreatedAtError(
                f"CreatedAt datetime must be in UTC timezone, got {self.value.tzinfo}"
            )


# Aliases for convenience and generic domain use
Email = CustomerEmail
Language = CustomerLanguage
Country = CustomerCountry
TimeZone = CustomerTimeZone
CustomerTimezone = CustomerTimeZone
