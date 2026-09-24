from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.application.device.update_device_activation import UpdateDeviceActivationHandler
from app.domain.repositories import DeviceRepository
from app.infrastructure.db.repositories.device_repository import SqlAlchemyDeviceRepository
from app.infrastructure.db.session import DbSessionDep


def get_device_repository(db: DbSessionDep) -> DeviceRepository:
    """Dependency provider returning a concrete DeviceRepository implementation."""
    return SqlAlchemyDeviceRepository(db)


DeviceRepositoryDep = Annotated[DeviceRepository, Depends(get_device_repository)]


def get_update_device_activation_handler(
    device_repository: DeviceRepositoryDep,
) -> UpdateDeviceActivationHandler:
    """Dependency provider returning the UpdateDeviceActivationHandler use case."""
    return UpdateDeviceActivationHandler(device_repository=device_repository)


UpdateDeviceActivationHandlerDep = Annotated[
    UpdateDeviceActivationHandler,
    Depends(get_update_device_activation_handler),
]
