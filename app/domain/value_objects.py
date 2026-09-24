from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Generic, TypeVar
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.exceptions import (
    InvalidCountryError,
    InvalidCustomerIdError,
    InvalidDeviceIdError,
    InvalidDeviceStatusError,
    InvalidEmailError,
    InvalidLanguageError,
    InvalidMeasurementIdError,
    InvalidMeasurementTypeError,
    InvalidMeasurementUnitError,
    InvalidMeasurementValueError,
    InvalidNameError,
    InvalidSerialNumberError,
    InvalidTimeZoneError,
    InvalidTimestampError,
)

T = TypeVar("T")

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_COUNTRY_REGEX = re.compile(r"^[A-Z]{2}$")
_LANGUAGE_REGEX = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")
_SERIAL_NUMBER_REGEX = re.compile(r"^[A-Za-z0-9_\-\.:]+$")


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
class DeviceId(ValueObject[UUID]):
    """Value object representing a device's unique identifier."""

    value: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if isinstance(self.value, str):
            try:
                object.__setattr__(self, "value", UUID(self.value))
            except (ValueError, TypeError, AttributeError) as exc:
                raise InvalidDeviceIdError(
                    f"Invalid UUID string for DeviceId: {self.value!r}"
                ) from exc
        elif not isinstance(self.value, UUID):
            raise InvalidDeviceIdError(
                f"DeviceId must be a UUID instance or valid UUID string, got {type(self.value).__name__}"
            )


@dataclass(frozen=True)
class Name(ValueObject[str]):
    """Value object representing a name."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidNameError(
                f"Name must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidNameError("Name cannot be empty or whitespace only")
        if len(self.value) > 255:
            raise InvalidNameError(
                f"Name cannot exceed 255 characters (got {len(self.value)})"
            )


@dataclass(frozen=True)
class Email(ValueObject[str]):
    """Value object representing an email address."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidEmailError(
                f"Email must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidEmailError("Email cannot be empty")
        if not _EMAIL_REGEX.match(trimmed):
            raise InvalidEmailError(f"Invalid email address format: {self.value!r}")


@dataclass(frozen=True)
class Language(ValueObject[str]):
    """Value object representing a language code (ISO 639-1 or BCP 47)."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidLanguageError(
                f"Language must be a string, got {type(self.value).__name__}"
            )
        if not _LANGUAGE_REGEX.match(self.value):
            raise InvalidLanguageError(
                f"Language must be a valid ISO 639-1 or BCP 47 code (e.g. 'en', 'en-US'), got {self.value!r}"
            )


@dataclass(frozen=True)
class Country(ValueObject[str]):
    """Value object representing a country code (ISO 3166-1 alpha-2)."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidCountryError(
                f"Country must be a string, got {type(self.value).__name__}"
            )
        if not _COUNTRY_REGEX.match(self.value):
            raise InvalidCountryError(
                f"Country must be a 2-letter uppercase ISO 3166-1 alpha-2 code (e.g. 'ES', 'US'), got {self.value!r}"
            )


@dataclass(frozen=True)
class TimeZone(ValueObject[str]):
    """Value object representing an IANA timezone."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidTimeZoneError(
                f"TimeZone must be a string, got {type(self.value).__name__}"
            )
        try:
            ZoneInfo(self.value)
        except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
            raise InvalidTimeZoneError(
                f"TimeZone must be a valid IANA Time Zone identifier (e.g. 'Europe/Madrid', 'UTC'), got {self.value!r}"
            ) from exc


@dataclass(frozen=True)
class SerialNumber(ValueObject[str]):
    """Value object representing a unique serial number."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidSerialNumberError(
                f"SerialNumber must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidSerialNumberError(
                "SerialNumber cannot be empty or whitespace only"
            )
        if len(trimmed) > 100:
            raise InvalidSerialNumberError(
                f"SerialNumber cannot exceed 100 characters (got {len(trimmed)})"
            )
        if not _SERIAL_NUMBER_REGEX.match(trimmed):
            raise InvalidSerialNumberError(
                f"Invalid serial number format: {self.value!r}. Only alphanumeric characters, hyphens, underscores, dots, and colons are allowed."
            )
        if trimmed != self.value:
            object.__setattr__(self, "value", trimmed)


class DeviceStatusEnum(str, Enum):
    """Enumeration of possible operational/connectivity states for an IoT device."""

    ONLINE = "online"
    OFFLINE = "offline"
    PROVISIONING = "provisioning"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DECOMMISSIONED = "decommissioned"


@dataclass(frozen=True)
class DeviceStatus(ValueObject[str]):
    """Value object representing an IoT device's operational/connection status."""

    value: str = DeviceStatusEnum.OFFLINE.value

    def __post_init__(self) -> None:
        if isinstance(self.value, DeviceStatusEnum):
            object.__setattr__(self, "value", self.value.value)
        elif isinstance(self.value, str):
            val = self.value.strip().lower()
            try:
                status_enum = DeviceStatusEnum(val)
                object.__setattr__(self, "value", status_enum.value)
            except ValueError as exc:
                valid_statuses = ", ".join(repr(s.value) for s in DeviceStatusEnum)
                raise InvalidDeviceStatusError(
                    f"Invalid device status {self.value!r}. Must be one of: {valid_statuses}"
                ) from exc
        else:
            raise InvalidDeviceStatusError(
                f"DeviceStatus must be a string or DeviceStatusEnum, got {type(self.value).__name__}"
            )

    @classmethod
    def online(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.ONLINE.value)

    @classmethod
    def offline(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.OFFLINE.value)

    @classmethod
    def provisioning(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.PROVISIONING.value)

    @classmethod
    def maintenance(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.MAINTENANCE.value)

    @classmethod
    def error(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.ERROR.value)

    @classmethod
    def decommissioned(cls) -> DeviceStatus:
        return cls(DeviceStatusEnum.DECOMMISSIONED.value)

    @property
    def is_online(self) -> bool:
        return self.value == DeviceStatusEnum.ONLINE.value

    @property
    def is_offline(self) -> bool:
        return self.value == DeviceStatusEnum.OFFLINE.value

    @property
    def is_connected(self) -> bool:
        return self.value == DeviceStatusEnum.ONLINE.value


@dataclass(frozen=True)
class Timestamp(ValueObject[datetime]):
    """Value object representing a timezone-aware UTC timestamp."""

    value: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise InvalidTimestampError(
                f"Timestamp must be a datetime instance, got {type(self.value).__name__}"
            )
        if self.value.tzinfo is None or self.value.utcoffset() is None:
            raise InvalidTimestampError("Timestamp datetime must be timezone-aware (UTC)")
        if self.value.utcoffset() != timezone.utc.utcoffset(None):
            raise InvalidTimestampError(
                f"Timestamp datetime must be in UTC timezone, got {self.value.tzinfo}"
            )

class CreatedAt(Timestamp):
    """Value object representing the creation timestamp of a domain entity."""


class UpdatedAt(Timestamp):
    """Value object representing the last-updated timestamp of a domain entity."""



@dataclass(frozen=True)
class MeasurementId(ValueObject[UUID]):
    """Value object representing a measurement's unique identifier."""

    value: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if isinstance(self.value, str):
            try:
                object.__setattr__(self, "value", UUID(self.value))
            except (ValueError, TypeError, AttributeError) as exc:
                raise InvalidMeasurementIdError(
                    f"Invalid UUID string for MeasurementId: {self.value!r}"
                ) from exc
        elif not isinstance(self.value, UUID):
            raise InvalidMeasurementIdError(
                f"MeasurementId must be a UUID instance or valid UUID string, got {type(self.value).__name__}"
            )


@dataclass(frozen=True)
class MeasurementType(ValueObject[str]):
    """Value object representing the type/category of a measurement (e.g. 'temperature', 'humidity')."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidMeasurementTypeError(
                f"MeasurementType must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidMeasurementTypeError(
                "MeasurementType cannot be empty or whitespace only"
            )
        if len(trimmed) > 100:
            raise InvalidMeasurementTypeError(
                f"MeasurementType cannot exceed 100 characters (got {len(trimmed)})"
            )
        if trimmed != self.value:
            object.__setattr__(self, "value", trimmed)


@dataclass(frozen=True)
class MeasurementValue(ValueObject[float]):
    """Value object representing the numeric value of a measurement."""

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise InvalidMeasurementValueError(
                f"MeasurementValue must be a numeric type, got {type(self.value).__name__}"
            )
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
class MeasurementUnit(ValueObject[str]):
    """Value object representing the unit of a measurement (e.g. '°C', 'hPa', '%')."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidMeasurementUnitError(
                f"MeasurementUnit must be a string, got {type(self.value).__name__}"
            )
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidMeasurementUnitError(
                "MeasurementUnit cannot be empty or whitespace only"
            )
        if len(trimmed) > 50:
            raise InvalidMeasurementUnitError(
                f"MeasurementUnit cannot exceed 50 characters (got {len(trimmed)})"
            )
        if trimmed != self.value:
            object.__setattr__(self, "value", trimmed)
