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

Database migrations follow a strict **forward-only** policy ([ADR 009](docs/decisions/009-forward-only-database-migrations.md)). Downgrading migrations is prohibited across all environments to prevent destructive data loss, schema desynchronization, and deployment failures. All schema changes (including rollbacks or fixes) must be applied as new forward migrations (`alembic upgrade head`).

```bash
make migrate                      # apply all pending migrations
make migration msg="add foo"      # auto-generate a new migration
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
tests/
├── unit/              # Unit tests (mocked infrastructure)
└── e2e/               # End-to-end tests (real database)
```

## Main Technical Decisions and Assumptions

For an in-depth architectural breakdown, see [Technical Decisions & Improvements](docs/technical-decisions-and-improvements.md).

### Architecture & Domain-Driven Design (DDD)
- **Hexagonal / Clean Architecture**: Strict separation across 4 layers (Domain, Application, Infrastructure, API). The domain layer is pure Python standard library with zero external framework dependencies.
- **Strict Value Object Composition**: Entities are composed strictly of immutable, self-validating Value Objects. No primitive type coercion occurs inside domain entities; conversion is strictly handled at the application and DTO boundaries.
- **Explicit Dependency Injection**: Handler and repository dependencies are wired explicitly via FastAPI dependency injection with typed annotations.

### Data Modeling & Integrity
- **Decoupled Device Lifecycle & Customer Assignment ([ADR 004](docs/decisions/004-device-customer-assignment.md))**: Devices are registered as independent physical hardware before being assigned to customers. Device timezone represents deployment context and is set on assignment and cleared on unassignment.
- **Localization Attributes**: Optional customer attributes (`country`, `language`, `timezone`) enable localized communications. Device `timezone` allows analyzing telemetry against local operating patterns while storing all data in UTC.
- **Cascade Deletion Rules ([ADR 004](docs/decisions/004-device-customer-assignment.md), [ADR 005](docs/decisions/005-customer-deletion-cascade.md))**: Deleting a customer orphans devices back to the unassigned hardware inventory (`ON DELETE SET NULL`), while telemetry records prevent accidental device deletion (`ON DELETE RESTRICT`).
- **Strict UTC & Native UUIDs**: All timestamps are timezone-aware UTC (`TIMESTAMPTZ` in PostgreSQL). Identifiers use native PostgreSQL `UUID` columns rather than strings.
- **Forward-Only Database Migrations ([ADR 009](docs/decisions/009-forward-only-database-migrations.md))**: Schema evolution is strictly forward-only. `downgrade()` across all migrations raises `NotImplementedError` to safeguard against destructive data loss, schema desynchronization, and automated rollback failures in CI/CD.

### Querying, Pagination & Idempotency
- **Keyset (Cursor-Based) Pagination ([ADR 002](docs/decisions/002-cursor-based-pagination.md), [ADR 008](docs/decisions/008-measurement-query-and-time-series-pagination.md))**: Opaque base64 cursors backed by composite indexes guarantee $O(1)$ query performance and prevent page drifting under concurrent writes.
- **Dual-Purpose Telemetry Querying ([ADR 008](docs/decisions/008-measurement-query-and-time-series-pagination.md))**: A high query limit ceiling (up to 5,000 records) allows frontends to retrieve continuous ranges for graphing in a single request without pagination loops, while cursor pagination protects memory.
- **Client-Driven Idempotency ([ADR 006](docs/decisions/006-business-rules-summary.md))**: Ingestion requires client-generated measurement UUIDs with database-level conflict handling (`ON CONFLICT (id) DO NOTHING`), safely supporting client retries.

### Concurrency Strategy
- **Pessimistic Row Locking**: Device assignment operations use pessimistic row locking (`SELECT FOR UPDATE`) within transactions to prevent concurrent assignment races.
- **Database Constraints as Concurrency Backstop**: Unique constraints on device serial numbers and customer emails act as the final defense against race conditions, mapped directly to HTTP 409 responses.

### Key Assumptions
- **Single-Tenant Local Scope**: Designed for local evaluation without distributed multi-tenant complexity.
- **Hardware-Centric Telemetry Lineage**: Measurements belong to physical hardware units; reassigning a device retains historical telemetry on the device.
- **Independent, Event-Driven Sensor Sampling (Narrow Table Approach)**: Onboard sensors are individual with different sampling rates and different change deltas (transmitting whenever triggered by a value change or when a time interval elapses). Because readings are produced asynchronously rather than in synchronized multi-sensor packets, telemetry is modeled and stored as individual sensor measurement records (one row per reading) rather than grouped by timestamp in JSON or JSONB columns.
- **Synchronous Ingestion Suitability**: Direct synchronous batch ingestion (up to 1,000 items) is assumed sufficient for moderate workloads without an intermediate broker.
- **UTC Authority**: UTC remains the universal source of truth for all ingestion and persistence.
- **Device HTTP Compatibility**: Connected hardware is assumed to interpret standard HTTP status codes and handle backoff appropriately.

## Known Limitations

### Missing Use Cases & Incomplete API Surface
- **Device Querying & Management**: No endpoints exist to list/search devices (`GET /devices`) with filters, inspect a single device (`GET /devices/{id}`), trigger status transitions (`PATCH /devices/{id}`), or delete devices (`DELETE /devices/{id}`).
- **Customer Lifecycle Operations**: No endpoints exist to delete customers (`DELETE /customers/{id}`), update customer profiles (`PUT`/`PATCH /customers/{id}`), or retrieve a customer's assigned devices (`GET /customers/{id}/devices`).
- **Telemetry Aggregation**: No server-side rollup endpoints (e.g. min, max, average over 1-hour or 1-day windows); clients must fetch and aggregate raw data points.

### Concurrency & Locking Bottlenecks
- **Database-Bound Concurrency**: Concurrency control relies on database row locks (`SELECT FOR UPDATE`), which can increase database connection wait times and restrict write throughput under high horizontal load.
- **Lack of Distributed Locking**: No external distributed lock manager exists to coordinate multi-step workflows across services without holding active database transactions.

### Ingestion & Connection Bottlenecks
- **Synchronous Telemetry Ingestion**: Direct HTTP-to-database ingestion tightly couples sensor traffic bursts to relational database write throughput and connection limits.
- **Connection Overhead (`NullPool`)**: The database engine uses `NullPool`, opening and closing physical database TCP connections on every request rather than maintaining a persistent connection pool.

### Query Scoping & Test Setup
- **Single-Device Query Scope**: Telemetry queries are strictly scoped to a single device at a time; fleet-wide or multi-device queries are not supported.
- **Test Suite Duplication**: Integration tests duplicate database seeding helpers rather than utilizing centralized test data builders (Object Mothers).

### Absence of Historical Audit Trail
- **No Assignment or Configuration History**: Device assignments, unassignments, and configuration updates overwrite records in place. There is no historical ledger tracking past ownership, transfer timelines, or previous device timezones for historical telemetry context.

### Basic Health Check
- **Static Health Check**: `/health` was the first endpoint built simply to verify the container was up and running when there was nothing else to check yet. It returns a static `{"status": "ok"}` without verifying database connectivity or connection pool health.

## What You Would Improve If You Had More Time

### Complete Missing Use Cases & Solidify API
- **Device API Surface**: Add fleet listing (`GET /devices`) with keyset pagination and filtering (status, customer, serial prefix), single device retrieval (`GET /devices/{id}`), status transitions (`PATCH /devices/{id}`), and guarded device deletion.
- **Customer API Surface**: Add customer deletion (`DELETE /customers/{id}`), profile updates (`PATCH /customers/{id}`), and customer device listing (`GET /customers/{id}/devices`).

### Distributed Concurrency & Locking
- **Distributed Mutex Service**: Introduce an independent distributed locking service behind an application port to coordinate resource mutations across replicas without holding long-lived database row locks.

### Test Architecture & Fixtures
- **Object Mother & Data Builders**: Implement centralized test data factories to streamline domain entity construction and database seeding across unit and integration tests.

### Asynchronous Event-Driven Ingestion
- **Decoupled Ingestion Pipeline**: Decouple ingestion from relational persistence using a message broker or queue (`202 Accepted` response with background consumer persistence) to absorb burst traffic.
- **Lightweight Protocols**: Add support for lightweight IoT streaming protocols to reduce HTTP connection overhead.

### Database Optimization & Retention
- **Retention & Archiving**: Implement automated data retention and archiving policies for historical telemetry.
- **Connection Pool Tuning**: Replace `NullPool` with a tuned, persistent connection pool supporting connection reuse and overflow limits.

### Security & Multi-Tenancy
- **Authentication & RBAC**: Add authentication with role-based access control distinguishing administrator and customer roles.
- **Tenant Isolation**: Enforce ownership verification or database row-level security so customers can only access their own devices and telemetry.
- **Rate Limiting**: Implement token bucket rate limiting on ingestion endpoints to safeguard against misbehaving devices.

### Observability & Health Checks
- **Structured JSON Logging**: Format application logs as structured JSON containing timestamp, log level, request ID, client IP, and handler context for ingestion into centralized log aggregators.
- **Tiered Health Probes**: Split `/health` into a shallow liveness probe (`/health/live`) to catch process hangs and a deep readiness probe (`/health/ready`) that checks database connectivity (`SELECT 1`) and pool capacity.

### Domain Event Publishing & Analytical Pipeline
- **Domain Event Publishing**: Emit domain events for lifecycle state transitions (assignments, status changes, configuration updates) via an event bus or outbox pattern.
- **Analytical Data Pipeline**: Stream events into an analytical data store or data lake to build an immutable audit trail, enable historical timezone reconstruction for telemetry analysis, and support business intelligence.

### Command & Query Bus (CQRS Dispatcher)
- **Unified Dispatcher**: Replace direct handler injection in API routes with a centralized Command and Query Bus.
- **Pluggable Middleware Pipeline**: Implement pipeline middleware for cross-cutting concerns (automatic transaction boundaries, structured logging, centralized authorization).
- **Multi-Transport Portability**: Allow the exact same application handlers and validation pipelines to be executed from background job workers, message consumers, or CLI tools without HTTP dependencies.

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

## Optional Technical Requirements

Detailed specifications and architectural designs for optional technical requirements can be found in the following documents:

- [API Authentication & Access Control](docs/api-authentication.md): Architecture and technical proposal covering user identity (JWT + refresh tokens), Role-Based Access Control (RBAC), and IoT edge device authentication (`X-Device-Token`).
- [Monitoring & Observability](docs/monitoring-and-observability.md): Guide detailing telemetry pillars (metrics, distributed tracing, structured JSON logs), dashboarding, and alerting standards for production IoT workloads.

