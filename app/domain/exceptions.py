from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain errors."""


class DomainValidationError(DomainError, ValueError):
    """Base exception for validation errors in domain entities and value objects."""


class InvalidCustomerIdError(DomainValidationError):
    """Raised when a CustomerId value is invalid."""


class InvalidCustomerNameError(DomainValidationError):
    """Raised when a CustomerName value is invalid."""


class InvalidCustomerEmailError(DomainValidationError):
    """Raised when a CustomerEmail value is invalid."""


class InvalidCustomerLanguageError(DomainValidationError):
    """Raised when a CustomerLanguage value is invalid."""


class InvalidCustomerCountryError(DomainValidationError):
    """Raised when a CustomerCountry value is invalid."""


class InvalidCustomerTimeZoneError(DomainValidationError):
    """Raised when a CustomerTimeZone value is invalid."""


class InvalidCreatedAtError(DomainValidationError):
    """Raised when a CreatedAt value is invalid."""
