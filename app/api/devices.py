from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import Field
from starlette import status

from app.api.dependencies import IngestMeasurementsHandlerDep, ListMeasurementsHandlerDep, UpdateDeviceActivationHandlerDep
from app.application.device.update_device_activation import UpdateDeviceActivationCommand
from app.application.measurement.ingest_measurements import (
    IngestMeasurementsCommand,
    MeasurementItem,
)
from app.application.measurement.list_measurements import ListMeasurementsQuery
from app.infrastructure.db.session import DbSessionDep
from app.schemas.device import DeviceActivationUpdate
from app.schemas.measurement import MeasurementIngestItem, MeasurementResponse, PaginatedMeasurementsResponse

router = APIRouter(prefix="/devices", tags=["Devices"])


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
