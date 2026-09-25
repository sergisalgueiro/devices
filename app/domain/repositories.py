from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from app.domain.customer import Customer
from app.domain.device import Device
from app.domain.measurement import Measurement

T = TypeVar("T")


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False


@dataclass(frozen=True)
class CustomerListFilters:
    email: str | None = None
    country: str | None = None
    language: str | None = None
    name: str | None = None


class DeviceRepository(ABC):
    """Abstract repository interface for Device persistence operations."""

    @abstractmethod
    async def get_by_id(self, device_id: UUID) -> Device | None:
        """Return the Device with the given id, or None if not found."""
        ...

    @abstractmethod
    async def save(self, device: Device) -> None:
        """Persist a new or updated Device."""
        ...


class CustomerRepository(ABC):
    """Abstract repository interface for Customer persistence operations."""

    @abstractmethod
    async def get_by_id(self, customer_id: UUID) -> Customer | None:
        """Return the Customer with the given id, or None if not found."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Customer | None:
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
    async def save(self, measurement: Measurement) -> None:
        """Persist a new Measurement."""
        ...

    @abstractmethod
    async def save_batch(self, measurements: list[Measurement]) -> int:
        """Persist a batch of measurements, skipping duplicates by id.

        Returns the number of newly inserted measurements.
        """
        ...
