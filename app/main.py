from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.devices import router as devices_router
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: disposes the async DB engine on shutdown."""
    yield
    await engine.dispose()


app = FastAPI(
    title="Device Management & Measurement API",
    description="API to manage customers, devices, and ingest/retrieve measurements.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(devices_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint to verify the service is up and running."""
    return {"status": "ok"}
