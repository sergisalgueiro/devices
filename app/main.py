import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.api.customers import router as customers_router
from app.api.devices import router as devices_router
from app.domain.exceptions import (
    CustomerEmailAlreadyExistsError,
    CustomerNotFoundError,
    DeviceNotFoundError,
    DomainError,
    DomainValidationError,
    InactiveDeviceError,
    SerialNumberAlreadyExistsError,
)
from app.infrastructure.db.session import engine
from app.infrastructure.logging import configure_logging

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup: Device Management API v0.1.0")
    yield
    logger.info("Application shutdown: disposing database engine")
    await engine.dispose()


app = FastAPI(
    title="Device Management & Measurement API",
    description="API to manage customers, devices, and ingest/retrieve measurements.",
    version="0.1.0",
    lifespan=lifespan,
)



@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(request: Request, exc: DeviceNotFoundError) -> JSONResponse:
    logger.warning("Device not found: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(InactiveDeviceError)
async def inactive_device_handler(request: Request, exc: InactiveDeviceError) -> JSONResponse:
    logger.warning("Inactive device: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


@app.exception_handler(DomainValidationError)
async def domain_validation_error_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
    logger.warning("Validation error: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    logger.error("Domain error: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s %s", request.method, request.url.path, exc_info=True)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


@app.exception_handler(CustomerNotFoundError)
async def customer_not_found_handler(request: Request, exc: CustomerNotFoundError) -> JSONResponse:
    logger.warning("Customer not found: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(CustomerEmailAlreadyExistsError)
async def customer_email_exists_handler(request: Request, exc: CustomerEmailAlreadyExistsError) -> JSONResponse:
    logger.warning("Customer email conflict: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(SerialNumberAlreadyExistsError)
async def serial_number_exists_handler(request: Request, exc: SerialNumberAlreadyExistsError) -> JSONResponse:
    logger.warning("Device serial number conflict: %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


app.include_router(customers_router)
app.include_router(devices_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint to verify the service is up and running."""
    return {"status": "ok"}
