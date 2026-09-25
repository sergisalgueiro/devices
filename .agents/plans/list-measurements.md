# Plan: List Measurements for a Device Endpoint

## Context

The project has a measurement ingestion endpoint (`POST /devices/{device_id}/measurements`) but no way to query measurements back. We need a read endpoint that returns paginated measurements for a device, with filtering by measurement type and time range. The project already has a complete cursor-based pagination pattern on the customers list endpoint — we'll replicate it exactly.

## Endpoint Design

`GET /devices/{device_id}/measurements`

- **Filters**: `type` (exact match), `start_time` (inclusive), `end_time` (exclusive)
- **Pagination**: cursor-based, reusing `PaginatedResult[T]` from `app/domain/repositories.py`
- **Sort**: by `timestamp` only, default `desc` (most recent first), configurable `asc`/`desc` via `sort_dir`
- **Limit**: 1–100, default 20
- **404** if device doesn't exist

## Implementation (in order)

### 1. Domain — `app/domain/repositories.py`

Add `MeasurementListFilters` frozen dataclass with optional fields: `type: str`, `start_time: datetime`, `end_time: datetime`.

Add abstract `list()` method to `MeasurementRepository`:
```python
async def list(self, device_id: UUID, filters: MeasurementListFilters, sort_field: str, sort_direction: str, limit: int, cursor: str | None) -> PaginatedResult[Measurement]
```

### 2. Application — create `app/application/measurement/list_measurements.py`

Following the pattern in `app/application/customer/list_customers.py`:

- `ListMeasurementsQuery` frozen dataclass: `device_id`, `type`, `start_time`, `end_time`, `sort_field="timestamp"`, `sort_direction="desc"`, `limit=20`, `cursor=None`
- `ListMeasurementsHandler` dataclass with `device_repository` + `measurement_repository`
- `handle()`: verify device exists (raise `DeviceNotFoundError` if not), build `MeasurementListFilters`, delegate to `measurement_repository.list()`

### 3. Infrastructure — `app/infrastructure/db/repositories/measurement_repository.py`

Add `list()` method mirroring `customer_repository.py` lines 95–154:

- Cursor encode/decode: base64url JSON with `{"f": "timestamp", "d": "desc", "v": "ISO8601", "id": "uuid"}`. Datetime via `.isoformat()` / `.fromisoformat()`.
- WHERE: always `device_id == device_id`, then conditionally `type ==`, `timestamp >=` start_time, `timestamp <` end_time
- Cursor continuation: compound `(timestamp < cursor_val) OR (timestamp == cursor_val AND id < cursor_id)` for desc (flip for asc)
- ORDER BY `timestamp` + `id` as tiebreaker (both same direction)
- Fetch `limit + 1`, slice, set `has_more`
- `_to_domain()` method to reconstitute `Measurement` from `MeasurementModel` using value objects

### 4. Schemas — `app/schemas/measurement.py`

Add (keeping existing `MeasurementIngestItem`):

- `MeasurementResponse`: fields `id`, `device_id`, `type`, `value`, `unit`, `timestamp` with `unwrap_value_objects` model_validator (same pattern as `CustomerResponse` in `app/schemas/customer.py:68-79`)
- `PaginatedMeasurementsResponse`: `items: list[MeasurementResponse]`, `next_cursor: str | None`, `has_more: bool`

### 5. Dependencies — `app/api/dependencies.py`

Add `get_list_measurements_handler()` (takes `DeviceRepositoryDep` + `MeasurementRepositoryDep`, returns `ListMeasurementsHandler`) and `ListMeasurementsHandlerDep` type alias. Same pattern as `get_ingest_measurements_handler()`.

### 6. API — `app/api/devices.py`

Add `GET /{device_id}/measurements` endpoint with query params:
- `type: str | None` — filter by measurement type
- `start_time: datetime | None` — inclusive lower bound
- `end_time: datetime | None` — exclusive upper bound
- `sort_dir: str` — pattern `^(asc|desc)$`, default `"desc"`
- `limit: int` — ge=1, le=100, default 20
- `cursor: str | None`

Constructs `ListMeasurementsQuery`, calls handler, maps result to `PaginatedMeasurementsResponse`.

### 7. Unit tests — create `tests/unit/application/test_list_measurements_handler.py`

Test cases:
- Device not found raises `DeviceNotFoundError`
- Delegates to repository with correct `MeasurementListFilters` (type, start_time, end_time)
- Passes sort/pagination params through (sort_direction, limit, cursor)
- Returns `PaginatedResult` with has_more metadata intact

### 8. E2E tests — create `tests/e2e/test_list_measurements_api.py`

Helper: `_seed_device()` and `_seed_measurement()` using direct SQLAlchemy inserts (pattern from existing E2E tests).

Test cases:
- 404 for nonexistent device
- 200 with empty list for device with no measurements
- Returns measurements for a device
- Filters by type (exact match)
- Filters by time range (start_time inclusive, end_time exclusive)
- Cursor pagination works across pages (disjoint items, correct ordering)
- Default sort is descending by timestamp
- Combined filters use AND logic
- Invalid `sort_dir` returns 422
- `limit` out of range returns 422

## Verification

1. Run unit tests: `docker compose exec api pytest tests/unit/application/test_list_measurements_handler.py -v`
2. Run E2E tests: `docker compose exec api pytest tests/e2e/test_list_measurements_api.py -v`
3. Run full test suite to check for regressions: `docker compose exec api pytest -v`
