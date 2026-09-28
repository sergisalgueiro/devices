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

## AI-Assisted Development

This project was developed with the assistance of AI coding tools, following rigorous engineering constraints, domain-driven design (DDD), and test-driven validation.

### 1. Tools Used
- **Antigravity**: Used with the suite of available models (including Gemini models) for contextual codebase reasoning, planning, architectural alignment, and implementation.
- **Claude Code**: Used with Sonnet 4.6 and Opus 4.6 for technical knowledge lookup, code generation, refactoring, and application logic.

### 2. What They Were Used For
- Scaffolding Clean Architecture / DDD layer separation (domain, application, infrastructure, API).
- Generating boilerplate for repositories, migrations, and Pydantic schemas.
- Accelerating test writing (unit tests for use case handlers and e2e acceptance tests for HTTP endpoints).
- Cross-referencing FastAPI, asyncpg, and SQLAlchemy 2.0 best practices.

### 3. Suggestions Changed or Rejected
- **Rejection of `__post_init__` Type Coercion in Domain Entities**:
  AI models often defaulted to Python's dynamic fluidity by allowing entity constructors to accept primitive types (`str`, `int`, naive `datetime`) and converting them internally inside `__post_init__`. This was explicitly rejected. Entities must strictly enforce invariant boundaries and accept only pre-validated, immutable Value Objects. Type coercion belongs in the application/DTO mapping layer, not the domain entities.
- **Correction of Device Unassignment Logic**:
  AI-generated unassignment logic initially detached the customer reference but failed to clean up the device's associated customer timezone. This was caught and corrected to ensure the timezone is explicitly cleared upon unassigning, preventing stale configuration leaks.

### 4. Code Validation Strategy
All AI-generated code was verified through a multi-tiered validation workflow:
1. **Container-First Execution**: Tests and commands were run strictly inside Docker Compose (`docker compose exec api pytest`) to eliminate host-environment discrepancies.
2. **Application Unit Tests**: Comprehensive unit tests for command and query handlers, testing both happy paths and domain violation error paths with mocked infrastructure.
3. **End-to-End (E2E) Integration Tests**: Tests exercising full HTTP endpoints against real PostgreSQL containers, verifying DI wiring, database migrations, cursor pagination, and HTTP status code mappings.
4. **Manual Verification**: Manual API testing via Swagger UI (`http://localhost:8000/docs`) and direct database inspection via `make db-shell` to verify response formats, headers, and persistence guarantees.

### 5. Agent Instructions & Skills Used
- **Project `AGENTS.md`**: The repository's root [`AGENTS.md`](AGENTS.md) defining architectural guidelines, strict UTC timezone rules, native PostgreSQL UUIDs, container-first workflows, and pure entity composition rules.
- **Claude Code `AGENTS.md`**: Custom global configuration defining model routing strategies and subagent orchestration.
- **FastAPI Skill (`.agents/skills/fastapi`)**: Guidance ensuring idiomatic FastAPI usage (e.g., `Annotated` dependencies, proper response modeling, async/sync boundary separation).
- **Personal DDD/Hexagonal Skill**: A custom skill dedicated to enforcing strict Hexagonal / Domain-Driven Design boundaries, immutability of Value Objects, and separation of concerns.
