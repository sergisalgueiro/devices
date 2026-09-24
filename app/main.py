from fastapi import FastAPI

app = FastAPI(
    title="Device Management & Measurement API",
    description="API to manage customers, devices, and ingest/retrieve measurements.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint to verify the service is up and running."""
    return {"status": "ok"}
