from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.application.customer.create_customer import CreateCustomerHandler
from app.application.customer.get_customer import GetCustomerHandler
from app.application.customer.list_customers import ListCustomersHandler
from app.application.device.update_device_activation import UpdateDeviceActivationHandler
from app.application.measurement.ingest_measurements import IngestMeasurementsHandler
from app.application.measurement.list_measurements import ListMeasurementsHandler
from app.domain.repositories import CustomerRepository, DeviceRepository, MeasurementRepository
from app.infrastructure.db.repositories.customer_repository import SqlAlchemyCustomerRepository
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


def get_list_measurements_handler(
    device_repository: DeviceRepositoryDep,
    measurement_repository: MeasurementRepositoryDep,
) -> ListMeasurementsHandler:
    """Dependency provider returning the ListMeasurementsHandler use case."""
    return ListMeasurementsHandler(
        device_repository=device_repository,
        measurement_repository=measurement_repository,
    )


ListMeasurementsHandlerDep = Annotated[
    ListMeasurementsHandler,
    Depends(get_list_measurements_handler),
]


def get_customer_repository(db: DbSessionDep) -> CustomerRepository:
    """Dependency provider returning a concrete CustomerRepository implementation."""
    return SqlAlchemyCustomerRepository(db)


CustomerRepositoryDep = Annotated[CustomerRepository, Depends(get_customer_repository)]


def get_create_customer_handler(
    customer_repository: CustomerRepositoryDep,
) -> CreateCustomerHandler:
    """Dependency provider returning the CreateCustomerHandler use case."""
    return CreateCustomerHandler(customer_repository=customer_repository)


CreateCustomerHandlerDep = Annotated[CreateCustomerHandler, Depends(get_create_customer_handler)]


def get_get_customer_handler(
    customer_repository: CustomerRepositoryDep,
) -> GetCustomerHandler:
    """Dependency provider returning the GetCustomerHandler use case."""
    return GetCustomerHandler(customer_repository=customer_repository)


GetCustomerHandlerDep = Annotated[GetCustomerHandler, Depends(get_get_customer_handler)]


def get_list_customers_handler(
    customer_repository: CustomerRepositoryDep,
) -> ListCustomersHandler:
    """Dependency provider returning the ListCustomersHandler use case."""
    return ListCustomersHandler(customer_repository=customer_repository)


ListCustomersHandlerDep = Annotated[ListCustomersHandler, Depends(get_list_customers_handler)]
