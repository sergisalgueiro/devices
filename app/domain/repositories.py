from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from app.domain.customer import Customer
from app.domain.device import Device
from app.domain.measurement import Measurement
from app.domain.value_objects import Country, CustomerId, DeviceId, Email, Language, MeasurementType, Name, SerialNumber

T = TypeVar("T")


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False


@dataclass(frozen=True)
class MeasurementListFilters:
    type: MeasurementType | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


@dataclass(frozen=True)
class CustomerListFilters:
    email: Email | None = None
    country: Country | None = None
    language: Language | None = None
    name: Name | None = None


class DeviceRepository(ABC):
    """Abstract repository interface for Device persistence operations."""

    @abstractmethod
    async def get_by_id(self, device_id: DeviceId) -> Device | None:
        """Return the Device with the given id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_id_for_update(self, device_id: DeviceId) -> Device | None:
        """Return the Device with the given id and acquire a row-level lock (SELECT FOR UPDATE)."""
        ...

    @abstractmethod
    async def get_by_serial_number(self, serial_number: SerialNumber) -> Device | None:
        """Return the Device with the given serial number, or None if not found."""
        ...

    @abstractmethod
    async def save(self, device: Device) -> None:
        """Persist a new or updated Device."""
        ...


class CustomerRepository(ABC):
    """Abstract repository interface for Customer persistence operations."""

    @abstractmethod
    async def get_by_id(self, customer_id: CustomerId) -> Customer | None:
        """Return the Customer with the given id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> Customer | None:
        """Return the Customer with the given email, or None if not found."""
        ...

    @abstractmethod
    async def save(self, customer: Customer) -> None:
        """Persist a new or updated Customer."""
        ...

    @abstractmethod
    async def list(
        self,
        filters: CustomerListFilters,
        sort_field: str,
        sort_direction: str,
        limit: int,
        cursor: str | None,
    ) -> PaginatedResult[Customer]:
        """Return a paginated, optionally filtered list of Customers."""
        ...


class MeasurementRepository(ABC):
    """Abstract repository interface for Measurement persistence operations."""

    @abstractmethod
    async def save_batch(self, measurements: list[Measurement]) -> int:
        """Persist a batch of measurements, skipping duplicates by id.

        Returns the number of newly inserted measurements.
        """
        ...

    @abstractmethod
    async def list(
        self,
        device_id: DeviceId,
        filters: MeasurementListFilters,
        sort_field: str,
        sort_direction: str,
        limit: int,
        cursor: str | None,
    ) -> PaginatedResult[Measurement]:
        """Return a paginated, optionally filtered list of Measurements for a device."""
        ...
