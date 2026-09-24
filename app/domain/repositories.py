from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.customer import Customer
from app.domain.device import Device
from app.domain.measurement import Measurement


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
    async def save(self, customer: Customer) -> None:
        """Persist a new or updated Customer."""
        ...


class MeasurementRepository(ABC):
    """Abstract repository interface for Measurement persistence operations."""

    @abstractmethod
    async def save(self, measurement: Measurement) -> None:
        """Persist a new Measurement."""
        ...
