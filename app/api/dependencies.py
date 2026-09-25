from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.application.device.update_device_activation import UpdateDeviceActivationHandler
from app.application.measurement.ingest_measurements import IngestMeasurementsHandler
from app.domain.repositories import DeviceRepository, MeasurementRepository
from app.infrastructure.db.repositories.device_repository import SqlAlchemyDeviceRepository
from app.infrastructure.db.repositories.measurement_repository import SqlAlchemyMeasurementRepository
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


def get_measurement_repository(db: DbSessionDep) -> MeasurementRepository:
    """Dependency provider returning a concrete MeasurementRepository implementation."""
    return SqlAlchemyMeasurementRepository(db)


MeasurementRepositoryDep = Annotated[MeasurementRepository, Depends(get_measurement_repository)]


def get_ingest_measurements_handler(
    device_repository: DeviceRepositoryDep,
    measurement_repository: MeasurementRepositoryDep,
) -> IngestMeasurementsHandler:
    """Dependency provider returning the IngestMeasurementsHandler use case."""
    return IngestMeasurementsHandler(
        device_repository=device_repository,
        measurement_repository=measurement_repository,
    )


IngestMeasurementsHandlerDep = Annotated[
    IngestMeasurementsHandler,
    Depends(get_ingest_measurements_handler),
]
