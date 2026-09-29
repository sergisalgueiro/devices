# 008 — Measurement Telemetry Query Strategy & Time-Series Pagination

**Status:** Accepted  
**Date:** 2026-09-29

## Context

The endpoint `GET /devices/{device_id}/measurements` allows clients to retrieve ingested measurements for a specific device, supporting filtering by measurement `type` and time range (`start_time`, `end_time`).

In IoT telemetry systems, measurement retrieval serves two fundamentally different use cases:
1. **Tabular Data Exploration / Audit Logging**:
   - Web UI data tables or operator log viewers.
   - Typically navigated page-by-page in reverse chronological order (`sort_dir=desc`, most recent first).
   - Small batch sizes (e.g., 20–50 items per page).
2. **Time-Series Graphing & Analytics**:
   - Visualizing trends on charts (e.g. Chart.js, Grafana, Plotly).
   - Displayed chronologically from left to right (`sort_dir=asc`).
   - Requires continuous blocks of data points across a bounded time window (e.g., hundreds or thousands of points for a 24-hour or 7-day view).

Under the initial implementation, `limit` was capped at `le=100`. While safe for table views, querying a 24-hour telemetry window for a device logging once per minute (1,440 data points) forced frontend clients to make **15 sequential HTTP round-trips** chaining `next_cursor` tokens before being able to render a single chart.

Removing pagination entirely is dangerous: unbounded queries on high-frequency IoT devices over months of data can attempt to fetch hundreds of thousands of rows, causing server Out-Of-Memory (OOM) crashes, database connection saturation, and browser freezes.

## Decision

We adopt a **pragmatic, dual-purpose query strategy (Approach 1)**:

1. **Retain Keyset (Cursor-Based) Pagination as a Safeguard**:
   - Keep cursor pagination (`items`, `next_cursor`, `has_more`) backed by the composite index `(device_id, timestamp, id)`.
   - The default `limit` remains `20` to keep table exploration lightweight.
2. **Expand the Limit Ceiling for Time-Series Consumption**:
   - Raise the maximum allowed `limit` from `100` to `5,000`.
   - Callers rendering graphs can query bounded time windows (`start_time` and `end_time`) with `limit=5000` and `sort_dir=asc`.
   - For typical graphing windows (e.g. 1-day or 7-day intervals at moderate sample frequencies), the entire dataset is returned in a single HTTP response with `has_more=false`.
   - If the time range contains more than 5,000 points, the cursor mechanism acts as a safety backstop, preventing server exhaustion while indicating to the caller that data was clipped.
3. **Defer Specialized Aggregation / Downsampling**:
   - Full time-series rollups, downsampling (e.g. bucketing via PostgreSQL `date_bin`), and separate aggregation endpoints are deferred until actual production sampling frequencies, retention policies, and visualization requirements are established.

## Rationale

- **Avoid Premature Complexity**: Building a complex aggregation engine or introducing a dedicated time-series database (e.g., TimescaleDB, InfluxDB) without known client aggregation specs (e.g., whether users need `avg`, `min`, `max`, `sum`, or `p95`, and at what bucket intervals: 1m, 5m, 1h) risks building the wrong abstractions.
- **Immediate Developer Experience Improvement**: Raising the ceiling to 5,000 immediately resolves the client-side N+1 pagination waterfall for charting, with minimal code surface changes.
- **Data Transfer Feasibility**: 5,000 JSON measurement records account for ~2–3 MB of payload, which PostgreSQL, SQLAlchemy, and FastAPI can stream and serialize in under 50 ms.
- **Backward Compatibility**: Fully backward-compatible with existing consumers and tests relying on `limit=20` and cursor headers.

## Trade-offs & Known Limitations

- **Browser & Network Overhead at High Density**: For devices with very high frequency (e.g., 10 Hz telemetry), 5,000 points covers only ~8 minutes of data. Transferring thousands of raw records with complete entity metadata (`id`, `device_id`, `type`, `unit`, `timestamp`, `value`) is redundant for graphs that only need `(timestamp, value)` pairs.
- **No Downsampling**: Screens typically have ~1,920 horizontal pixels; plotting 5,000+ SVG or canvas elements can strain client-side rendering.

## Future Evolution Trigger

When telemetry volume, device frequency, and reporting requirements become clearly defined:
1. **Dedicated Time-Series Endpoint**: Introduce `GET /devices/{id}/measurements/timeseries` or `GET /devices/{id}/measurements/aggregates`.
2. **Database-Level Bucketing**: Utilize PostgreSQL's `date_bin('5 minutes', timestamp, ...)` or `date_trunc()` to compute min, max, avg, and sample counts per bucket window.
3. **Compact Projections**: Return columnar or compact tuple formats `{"timestamps": [...], "values": [...]}` to minimize bandwidth.
