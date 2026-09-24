from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain errors."""


class DomainValidationError(DomainError, ValueError):
    """Base exception for validation errors in domain entities and value objects."""


class InvalidCustomerIdError(DomainValidationError):
    """Raised when a CustomerId value is invalid."""


class InvalidDeviceIdError(DomainValidationError):
    """Raised when a DeviceId value is invalid."""


class InvalidNameError(DomainValidationError):
    """Raised when a Name value is invalid."""


class InvalidEmailError(DomainValidationError):
    """Raised when an Email value is invalid."""


class InvalidLanguageError(DomainValidationError):
    """Raised when a Language value is invalid."""


class InvalidCountryError(DomainValidationError):
    """Raised when a Country value is invalid."""


class InvalidTimeZoneError(DomainValidationError):
    """Raised when a TimeZone value is invalid."""


class InvalidSerialNumberError(DomainValidationError):
    """Raised when a SerialNumber value is invalid."""


class InvalidDeviceStatusError(DomainValidationError):
    """Raised when a DeviceStatus value is invalid."""


class InvalidCreatedAtError(DomainValidationError):
    """Raised when a CreatedAt value is invalid."""


class InvalidUpdatedAtError(DomainValidationError):
    """Raised when an UpdatedAt value is invalid."""

