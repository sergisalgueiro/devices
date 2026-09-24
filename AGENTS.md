# Project Guidelines & Coding Standards

## 1. Stack & Architecture
- **Framework**: FastAPI (async).
- **ORM & DB**: SQLAlchemy 2.0 (asyncpg) + PostgreSQL 17 + Alembic.
- **Pattern**: Clean Architecture / DDD:
  - `app/domain/`: Pure domain entities, value objects, exceptions, and repository interfaces. Pure Python (standard library `dataclasses`, `typing`, `uuid`, `datetime`). Zero dependencies on web frameworks or ORMs.
  - `app/application/`: Application use cases, service orchestration, DTOs.
  - `app/infrastructure/`: Database models (SQLAlchemy), repository implementations, database sessions, external integrations.
  - `app/main.py` / API routers: FastAPI endpoints, HTTP request/response schemas (Pydantic).

---

## 2. Datetime & Timezone Rules (Strict UTC)
- **Always Timezone-Aware UTC**: Never use naive `datetime.now()` or deprecated `datetime.utcnow()`.
- **Python**: Use `datetime.now(timezone.utc)` from standard library `datetime`.
- **SQLAlchemy / DB Models**: Always use `sa.DateTime(timezone=True)` so PostgreSQL creates `TIMESTAMPTZ` columns.
- **Containers & Environment**: `TZ=UTC` is enforced across all services.

---

## 3. Identifiers & UUIDs
- **Domain**: Use Python standard library `uuid.UUID` (`from uuid import UUID, uuid4`).
- **PostgreSQL / SQLAlchemy**: Use native PostgreSQL `UUID` type via `sa.UUID(as_uuid=True)`, not `VARCHAR(36)`.

---

## 4. Testing Strategy & Container-First Workflow

### 4.1 Container-First Execution Rules
- **Execute Exclusively in Containers**: Never run tests, migrations, or Python commands directly on the host machine. Always execute commands inside the container via Docker Compose:
  ```bash
  docker compose exec api pytest
  ```
- **Applies to All Test Levels**: Container-first execution applies across the entire testing pyramid — unit tests, integration tests, and end-to-end (e2e) tests.
- **Mandatory Validation**: Always run and validate the test suite inside the container after making changes before considering any task finished or closed.
- **Testing Stack**: Pytest (`pytest`, `pytest-asyncio`, `httpx.AsyncClient`).
- **Typing**: Use standard Python type annotations (`dict[str, Any]`, `list[str]`, `UUID`, etc.).
- **Async**: Use async/await for I/O operations (database queries, external HTTP calls).

### 4.2 Unit Tests (Application Layer)
Every command handler and query handler must have its own unit test file covering:
- **Happy path**: The handler produces the expected result given valid input.
- **Domain rule violations**: Each business rule that can reject the operation has at least one test case.
- **Edge cases**: Boundary values, empty collections, optional fields absent.

Unit tests mock infrastructure (repositories, publishers, external clients) and verify only application + domain logic.
Domain structs do not have unit tests. Value objects, aggregates, and domain events are exercised through application-layer tests. A standalone test file for a domain struct is a sign the logic belongs in the application layer or the test is redundant.

### 4.3 Acceptance / Integration Tests (Happy Path)
Every feature must include at least one end-to-end test that exercises the full stack (HTTP handler or consumer → application → infrastructure → real database/queue):
- **Proves layer wiring**: Proves all layers are wired correctly (DI, routing, serialisation, persistence).
- **Real infrastructure**: Uses real infrastructure (database, queues via LocalStack) — never mocked.
- **Primary success scenario**: Covers the primary success scenario that a user or upstream service would trigger.

### 4.4 Acceptance / Integration Tests (Key Failure Paths)
Include integration tests for failure scenarios that depend on infrastructure state or external service behaviour:
- **Entity not found**: (404 / domain error translation).
- **Authentication / authorisation denied**: (401 / 403).
- **External service failure**: (timeout, error response from a dependency).

These are distinct from unit-test domain violations because they verify that the infrastructure layer translates failures correctly.

---

## 5. Domain Modelling — Value Objects
Value objects wrap primitives and enforce validity at construction time. They are identified by their value, not by identity.
- **Validation in Constructor**: Validation happens in the constructor (`__post_init__` / `__init__`) — constructor returns the valid VO or raises a domain error (`DomainValidationError`) when input is invalid.
- **Immutable**: No setters (`@dataclass(frozen=True)`).
- **Equality by Value**: Equality is structural (`__eq__` evaluates value equality).
- **Primitive Accessor**: Expose an accessor (`.value`) to retrieve the underlying primitive.
- **Pure Standard Library**: Zero dependencies on external libraries or frameworks (use standard library `dataclasses`, `zoneinfo`, `re`, `uuid`, `datetime`).
