from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import Field
from starlette import status

from app.api.dependencies import AssignDeviceCustomerHandlerDep, CreateDeviceHandlerDep, IngestMeasurementsHandlerDep, ListMeasurementsHandlerDep, UnassignDeviceCustomerHandlerDep, UpdateDeviceActivationHandlerDep
from app.application.device.assign_device_customer import AssignDeviceCustomerCommand
from app.application.device.create_device import CreateDeviceCommand
from app.application.device.unassign_device_customer import UnassignDeviceCustomerCommand
from app.application.device.update_device_activation import UpdateDeviceActivationCommand
from app.application.measurement.ingest_measurements import (
    IngestMeasurementsCommand,
    MeasurementItem,
)
from app.application.measurement.list_measurements import ListMeasurementsQuery
from app.infrastructure.db.session import DbSessionDep
from app.schemas.device import AssignCustomerRequest, DeviceActivationUpdate, DeviceCreate, DeviceResponse
from app.schemas.measurement import MeasurementIngestItem, MeasurementResponse, PaginatedMeasurementsResponse

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new device",
)
async def create_device(
    payload: DeviceCreate,
    db: DbSessionDep,
    handler: CreateDeviceHandlerDep,
) -> DeviceResponse:
    """
    Register a new device. The device is created without a customer assignment.

    - `serial_number` must be unique across all devices.
    - Returns **409** if the serial number is already registered.
    - Returns **422** if payload validation fails.
    """
    async with db.begin():
        device = await handler.handle(CreateDeviceCommand(serial_number=payload.serial_number))
    return DeviceResponse.model_validate(device)


@router.put(
    "/{device_id}/customer",
    summary="Assign device to a customer",
)
async def assign_device_customer(
    device_id: UUID,
    payload: AssignCustomerRequest,
    db: DbSessionDep,
    handler: AssignDeviceCustomerHandlerDep,
) -> DeviceResponse:
    """
    Assign a device to a customer, optionally setting a timezone.

    - Idempotent: re-assigning to the same or a different customer is always accepted.
    - Returns **404** if the device or customer does not exist.
    - Returns **422** if payload validation fails.
    """
    async with db.begin():
        device = await handler.handle(
            AssignDeviceCustomerCommand(
                device_id=device_id,
                customer_id=payload.customer_id,
                timezone=str(payload.timezone) if payload.timezone is not None else None,
            )
        )
    return DeviceResponse.model_validate(device)


@router.delete(
    "/{device_id}/customer",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unassign device from its customer",
)
async def unassign_device_customer(
    device_id: UUID,
    db: DbSessionDep,
    handler: UnassignDeviceCustomerHandlerDep,
) -> None:
    """
    Remove the customer assignment from a device and clear its timezone.

    - Idempotent: unassigning an already-unassigned device is a successful no-op.
    - Returns **404** if the device does not exist.
    """
    async with db.begin():
        await handler.handle(UnassignDeviceCustomerCommand(device_id=device_id))


@router.patch(
    "/{device_id}/activation",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update device activation status",
)
async def update_device_activation(
    device_id: UUID,
    payload: DeviceActivationUpdate,
    db: DbSessionDep,
    handler: UpdateDeviceActivationHandlerDep,
) -> None:
    """
    Update the activation status of a device (activate or deactivate).

    - Setting `is_active: true` enables measurement ingestion.
    - Setting `is_active: false` prevents further measurement ingestion.
    - Idempotent: repeating the same target state is a successful no-op.
    - Returns **404** if the device does not exist.
    """
    async with db.begin():
        await handler.handle(
            UpdateDeviceActivationCommand(
                device_id=device_id,
                is_active=payload.is_active,
            )
        )


@router.post(
    "/{device_id}/measurements",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest device measurements",
)
async def ingest_measurements(
    device_id: UUID,
    payload: Annotated[list[MeasurementIngestItem], Field(min_length=1, max_length=1000)],
    db: DbSessionDep,
    handler: IngestMeasurementsHandlerDep,
) -> None:
    """
    Ingest a batch of measurements for a device.

    - The client provides a unique `measurement_id` per measurement for idempotency.
    - Duplicate `measurement_id` values are silently ignored (no duplicates created).
    - Accepts between 1 and 1,000 measurements per request. Larger payloads must be chunked.
    - Returns **201 Created** on success (even for fully duplicate batches).
    - Returns **404** if the device does not exist.
    - Returns **422** if the device is inactive or payload validation fails.
    """
    async with db.begin():
        await handler.handle(
            IngestMeasurementsCommand(
                device_id=device_id,
                measurements=[
                    MeasurementItem(
                        measurement_id=item.measurement_id,
                        type=item.type,
                        value=item.value,
                        unit=item.unit,
                        timestamp=item.timestamp,
                    )
                    for item in payload
                ],
            )
        )


@router.get(
    "/{device_id}/measurements",
    summary="List device measurements",
)
async def list_measurements(
    device_id: UUID,
    handler: ListMeasurementsHandlerDep,
    type: Annotated[str | None, Query(description="Filter by exact measurement type")] = None,
    start_time: Annotated[datetime | None, Query(description="Inclusive lower bound on timestamp (UTC)")] = None,
    end_time: Annotated[datetime | None, Query(description="Exclusive upper bound on timestamp (UTC)")] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$", description="Sort direction")] = "desc",
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum results per page")] = 20,
    cursor: Annotated[str | None, Query(description="Opaque pagination cursor from previous response")] = None,
) -> PaginatedMeasurementsResponse:
    """
    List measurements for a device with optional filters and cursor-based pagination.

    - Results are sorted by timestamp, most recent first by default.
    - Filters combine with AND logic.
    - Returns **404** if the device does not exist.
    - Returns **422** if query parameters fail validation.
    """
    result = await handler.handle(
        ListMeasurementsQuery(
            device_id=device_id,
            type=type,
            start_time=start_time,
            end_time=end_time,
            sort_direction=sort_dir,
            limit=limit,
            cursor=cursor,
        )
    )
    return PaginatedMeasurementsResponse(
        items=[MeasurementResponse.model_validate(m) for m in result.items],
        next_cursor=result.next_cursor,
        has_more=result.has_more,
    )
