# Devices API

IoT device management API built with FastAPI, SQLAlchemy 2.0, and PostgreSQL 17. Manages customers, devices, and device measurements following Clean Architecture / DDD patterns.

## Tech Stack

- **Python 3.12** / **FastAPI** / **Uvicorn**
- **SQLAlchemy 2.0** (async via asyncpg) + **Alembic** migrations
- **PostgreSQL 17**
- **Docker Compose** for local development

## Quick Start

```bash
make up    # creates .env (if missing), starts PostgreSQL + API, runs migrations
```

The API is available at http://localhost:8000.

Migrations run automatically on container startup via `AUTO_MIGRATE=true` (set in docker-compose for local dev). In production, remove this variable and run migrations explicitly as a pipeline step.

## Running the Application

```bash
make up           # start all services (detached)
make down         # stop all services
make restart      # restart the API container
make logs         # tail API logs
make ps           # list running containers
make shell        # bash shell inside the API container
make db-shell     # psql shell into PostgreSQL
```

The API runs with hot-reload enabled — code changes are picked up automatically.

## Running the Tests

All tests run inside the container:

```bash
make test         # run the full test suite
make test-v       # run tests with verbose output
```

## Database Migrations

```bash
make migrate                      # apply all pending migrations
make migration msg="add foo"      # auto-generate a new migration
make rollback                     # rollback the last migration
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json (also exported to [`docs/openapi.json`](docs/openapi.json))

To regenerate the static OpenAPI spec after endpoint changes:

```bash
make openapi
```

## API Endpoints

For detailed request/response schemas and interactive testing, see the [Swagger UI](http://localhost:8000/docs) or the static [OpenAPI spec](docs/openapi.json).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/customers` | Create a customer |
| `GET` | `/customers` | List customers (cursor-paginated) |
| `GET` | `/customers/{customer_id}` | Get a customer |
| `POST` | `/devices` | Create a device |
| `PUT` | `/devices/{device_id}/customer` | Assign device to customer |
| `DELETE` | `/devices/{device_id}/customer` | Unassign device from customer |
| `PATCH` | `/devices/{device_id}/activation` | Activate / deactivate device |
| `POST` | `/devices/{device_id}/measurements` | Ingest measurements (batch) |
| `GET` | `/devices/{device_id}/measurements` | List measurements (cursor-paginated) |

## Project Structure

```
app/
├── domain/            # Pure domain: entities, value objects, exceptions, repository interfaces
├── application/       # Use cases: command/query handlers, DTOs
├── infrastructure/    # SQLAlchemy models, repository implementations, DB session
├── api/               # FastAPI routers and dependencies
├── schemas/           # Pydantic request/response models
└── main.py            # Application entry point
migrations/
└── versions/          # Alembic migration scripts
docs/
├── openapi.json       # Exported OpenAPI spec
├── decisions/         # Architecture Decision Records
├── code-review.md
└── database-mechanisms.md
tests/
├── unit/              # Unit tests (mocked infrastructure)
└── e2e/               # End-to-end tests (real database)
```
