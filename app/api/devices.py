from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import Field
from starlette import status

from app.api.dependencies import IngestMeasurementsHandlerDep, UpdateDeviceActivationHandlerDep
from app.application.device.update_device_activation import UpdateDeviceActivationCommand
from app.application.measurement.ingest_measurements import (
    IngestMeasurementsCommand,
    MeasurementItem,
)
from app.domain.exceptions import DeviceNotFoundError, InactiveDeviceError
from app.infrastructure.db.session import DbSessionDep
from app.schemas.device import DeviceActivationUpdate
from app.schemas.measurement import MeasurementIngestItem

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
        try:
            await handler.handle(
                UpdateDeviceActivationCommand(
                    device_id=device_id,
                    is_active=payload.is_active,
                )
            )
        except DeviceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc


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
        try:
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
        except DeviceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except InactiveDeviceError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
