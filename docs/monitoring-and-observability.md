# Monitoring and Observability Guide — Devices API

> **Scope**: Observability architecture, telemetry standards, dashboard design, and prioritized alerting for the `devices` API project.  
> **Approach**: Technology-agnostic. Principles apply to any observability backend (open-source or managed SaaS).

---

## 1. Overview & Core Philosophy

For a production IoT device and measurement ingestion service, monitoring and observability serve two distinct needs:

- **Monitoring**: Tells us *if* the system is working (black-box symptoms: error rates, response times, saturated pools).
- **Observability**: Lets us understand *why* an unexpected failure is happening (white-box diagnostics: tracing slow queries, correlating error logs across requests).

To achieve full visibility without alert fatigue or high storage overhead, the platform is built on three correlated pillars:

```
                            THE THREE OBSERVABILITY PILLARS
┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
│          METRICS          │   │          TRACES           │   │      STRUCTURED LOGS      │
│  "What is breaking & how  │   │  "Where is the bottleneck │   │  "Why did it break?"      │
│   fast are we burning?"   │   │   across the call graph?" │   │  Detailed context, error  │
│  Aggregatable time-series │   │  Request lifecycle spans  │   │  stack, payload metadata  │
└─────────────┬─────────────┘   └─────────────┬─────────────┘   └─────────────┬─────────────┘
              │                               │                               │
              └───────────────────────┬───────┴───────────────────────────────┘
                                      ▼
                        CORRELATION (trace_id & span_id)
      Hover on metric spike ──> Click trace exemplar ──> Inspect correlated logs
```

---

## 2. The Three Telemetry Pillars

### 2.1 Metrics
Metrics are numeric measurements aggregated over time to evaluate health, traffic, and resource usage.

- **The RED Method (for APIs & Handlers)**:
  - **Rate**: Request throughput (req/s).
  - **Errors**: Failed requests (4xx client errors vs. 5xx server faults).
  - **Duration**: Latency distributions (**p50, p90, p95, p99**).
- **The USE Method (for Resources & Pools)**:
  - **Utilization**: % of time or capacity used (CPU, DB connections, memory).
  - **Saturation**: Queued work waiting for resources (DB pool wait queue, event loop lag).
  - **Errors**: Failures at resource level (connection timeouts, OOM kills).

> **Critical Rule — High Cardinality Protection**: Metric labels must **never** include high-cardinality dynamic values (such as `device_id`, `customer_id`, or raw URLs like `/devices/123/measurements`). Always use normalized route templates (e.g. `/devices/{id}/measurements`). Dynamic IDs belong strictly in traces and logs.

---

### 2.2 Distributed Tracing
Distributed tracing tracks an individual request as it travels through the system.

- **Spans**: Capture execution time for distinct segments:
  - Total HTTP request duration.
  - Authentication and token validation.
  - Database connection acquisition from the pool.
  - SQL query execution (`SELECT`, `INSERT`, `UPDATE`).
- **Context Propagation**: Standard trace headers (such as `traceparent`) propagate context between services and background tasks.
- **Exemplars**: Trace IDs attached directly to metric latency histograms, allowing an engineer to click on a latency spike in a chart and jump directly into the offending trace waterfall.

---

### 2.3 Structured JSON Logging
All application logs are formatted as single-line structured JSON emitted to `stdout`.

#### Standard Log Schema
```json
{
  "timestamp": "2026-09-30T10:15:30.125Z",
  "level": "ERROR",
  "service": "devices-api",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "request_id": "req-98f12a34-2e4b",
  "method": "POST",
  "route": "/devices/{id}/measurements",
  "status_code": 500,
  "duration_ms": 215.4,
  "device_id": "8a1b2c3d-4e5f-11ef-9876-0242ac120002",
  "error_type": "asyncpg.exceptions.PoolTimeoutError",
  "message": "Connection acquisition timed out after 5.0s (pool saturated)"
}
```

#### Logging Rules
1. **Correlation**: Every log generated inside a request must include `trace_id` and `span_id`.
2. **Zero PII**: Passwords, auth tokens (`Authorization`, `X-API-Key`), and customer emails must be scrubbed or masked before emission.
3. **Appropriate Log Levels**:
   - `ERROR`: Unhandled exceptions, failed DB queries, connection timeouts.
   - `WARNING`: Handled domain conflicts (e.g. inactive device, 404 not found, validation error).
   - `INFO`: Lifecycle milestones (app startup, shutdown, batch committed).
   - `DEBUG`: Verbose query execution (disabled in production).

---

## 3. What to Monitor in the Devices API

The following telemetry matrix defines the vital signals across all application layers:

### 3.1 Application & HTTP Layer (FastAPI)
| Metric | Type | Dimensions | Purpose & Target |
|---|---|---|---|
| `http_requests_total` | Counter | `method`, `route`, `status_code` | Request rate & error ratio. |
| `http_request_duration_seconds` | Histogram | `method`, `route` | Latency distribution (**p50, p90, p95, p99**). Target: p95 < 150ms. |
| `in_flight_requests` | Gauge | `route` | In-progress requests currently handled by the ASGI event loop. |
| `event_loop_lag_seconds` | Gauge | — | Event loop execution delay. Detects accidental blocking I/O. Target < 15ms. |
| `unhandled_exceptions_total` | Counter | `exception_type`, `route` | Total unexpected 500 errors. Target: 0. |
| `log_messages_total` | Counter | `level` (`ERROR`, `WARNING`, `INFO`), `module` | Track emission rates by log level to detect silent errors and internal failures. |

### 3.2 Database & Connection Pool Layer (PostgreSQL & asyncpg)
| Metric | Type | Dimensions | Purpose & Target |
|---|---|---|---|
| `db_pool_active_connections` | Gauge | `pool_name` | Connections currently in use by active transactions. |
| `db_pool_idle_connections` | Gauge | `pool_name` | Available connections standing idle in the pool. |
| `db_pool_wait_queue_length` | Gauge | `pool_name` | Requests waiting for an available DB connection. **Critical Target: 0.** |
| `db_pool_wait_duration_seconds` | Histogram | `pool_name` | Wait time to acquire a connection. Spikes indicate pool starvation. |
| `db_query_duration_seconds` | Histogram | `operation` (`SELECT`, `INSERT`) | Query execution latency. Target: p95 < 20ms. |
| `db_deadlocks_total` | Counter | — | PostgreSQL deadlocks. Target: 0. |

### 3.3 Domain & Telemetry Ingestion Layer
| Metric | Type | Dimensions | Purpose & Target |
|---|---|---|---|
| `measurements_ingested_total` | Counter | `measurement_type` | Ingestion throughput (points committed per second). |
| `measurement_batch_size` | Histogram | — | Count of measurements per ingestion payload. |
| `idempotency_conflicts_total` | Counter | `operation` | Duplicates deduplicated via `ON CONFLICT DO NOTHING`. Detects retry storms. |
| `measurement_clock_skew_seconds`| Histogram | — | $\lvert T_{\text{server}} - T_{\text{device}} \rvert$. Detects drifting hardware clocks on devices. |
| `active_devices_count` | Gauge | `status` (`online`, `offline`) | Number of distinct devices reporting within keepalive window. |

### 3.4 Host, Container & Compute Layer
| Metric | Type | Dimensions | Purpose & Target |
|---|---|---|---|
| `container_cpu_usage_ratio` | Gauge | `container` | CPU consumed vs. requested/limit. Warning > 80%. |
| `container_cpu_throttled_ratio` | Gauge | `container` | % of execution periods throttled by OS scheduler. Target < 5%. |
| `container_memory_usage_bytes` | Gauge | `container` | Physical RAM used vs. container limit. |
| `container_restarts_total` | Counter | `container` | Crash loops and OOM kills. Target: 0. |

---

## 4. How to Detect Issues

### 4.1 Service Level Objectives (SLOs) & Multi-Burn-Rate Alerting
Rather than alerting on noisy single-minute thresholds, alert on the speed at which your **Error Budget** is consumed:

- **Availability SLO**: $99.9\%$ of valid requests succeed over 30 days (Error Budget = $0.1\%$).
- **Latency SLO**: $99.0\%$ of requests complete in $\le 200\text{ms}$ over 30 days.

```
Burn Rate (B) = Speed of error budget consumption (1x burns 100% budget in 30 days)
├── 14.4x Burn Rate: Consumes 2% of budget in 1 hour  ──> P1 CRITICAL (Immediate Page)
├── 6.0x Burn Rate:  Consumes 5% of budget in 6 hours ──> P1 CRITICAL (Immediate Page)
└── 1.0x Burn Rate:  Consumes 10% of budget in 3 days ──> P2 MAJOR    (Incident Notification)
```

### 4.2 Dynamic Anomaly Detection
IoT device traffic follows natural daily patterns (higher during peak usage hours, lower at night). Static request thresholds trigger false alarms during off-peak periods.

- **Dynamic Baselines**: Continuously compare incoming traffic volume against historical trends for the same day and time.
- **Drop Anomaly (Outage)**: Alerts when ingestion drops significantly below expected historical volume, indicating widespread edge connectivity issues or upstream network outages.
- **Surge Anomaly (Retry Storm)**: Alerts when traffic unexpectedly spikes far above normal levels, detecting edge reconnection surges or device retry loops.

### 4.3 Tiered Health Checks & Synthetic Canaries
1. **Liveness Probe (`/health` or `/health/live`)**:
   - Zero-dependency check. Returns `{"status": "ok"}` immediately to verify the process is alive.
2. **Readiness Probe (`/health/ready`)**:
   - Executes an async `SELECT 1` on the database pool with a 2-second timeout and checks pool availability.
   - If the DB is unreachable, returns `503 Service Unavailable` so load balancers stop routing traffic to this instance.
3. **Synthetic Canary Worker**:
   - An automated test worker executes a full round-trip transaction every 60 seconds: writes a synthetic measurement and immediately reads it back.
   - Two consecutive failures trigger an immediate critical alert before real users notice.

### 4.4 Error Log Surge & Silent Failure Detection
Resilient systems frequently handle errors gracefully (e.g., fallback responses, circuit breaking, best-effort async tasks, background workers) without returning HTTP 5xx responses. Consequently, user-facing availability SLOs can remain green even when subsystems are failing internally.

- **Log-Derived Metric (`log_messages_total{level="ERROR"}`)**: Convert structured log emissions into a counter metric or monitor them directly via log aggregator metric filters.
- **Sustained Error Rate**: Trigger alerts when the rate of emitted `ERROR` logs exceeds baseline levels over a sustained window.
- **Background Worker & Consumer Coverage**: Catches fatal loops and uncaught exceptions in non-HTTP pipelines (e.g., event listeners, scheduled tasks, queue consumers) that lack HTTP status codes.
- **Log Hygiene Prerequisite**: Strict compliance with log levels is required—`ERROR` must be reserved solely for actionable system faults and unhandled failures, avoiding alert fatigue from expected client errors.

---

## 5. Dashboard Design: What It Should Contain

A production dashboard must be structured hierarchically so an engineer can diagnose an issue in seconds:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ ROW 1: EXECUTIVE HEALTH & SLO STATUS (Top-Level State)                                 │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────────────┐ │
│ │ 30-Day Availability SLO │ │ 30-Day Latency SLO      │ │ Active Alerts & Devices    │ │
│ │ 99.94% [HEALTHY]        │ │ 99.18% [HEALTHY]        │ │ 0 Critical | 12,450 Online │ │
│ └─────────────────────────┘ └─────────────────────────┘ └────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ROW 2: INGRESS & HTTP RED METRICS (FastAPI Core)                                       │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────────────┐ │
│ │ Request Rate (req/s)    │ │ Latency Percentiles (ms)│ │ Error Rates by Normalized    │ │
│ │ By method & route       │ │ p50, p90, p95, p99 +    │ │ Route (4xx vs 5xx)           │ │
│ │                         │ │ Trace Exemplars (dots)  │ │ (e.g. /devices/{id}/measure) │ │
│ └─────────────────────────┘ └─────────────────────────┘ └────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ROW 3: DATABASE & CONNECTION POOL (PostgreSQL / asyncpg)                               │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────────────┐ │
│ │ Pool Wait Queue Length  │ │ Active vs. Idle Conns   │ │ Query Duration (p95/p99)     │ │
│ │ (Must be 0)             │ │ Against Pool Max Limit  │ │ By SQL Operation             │ │
│ └─────────────────────────┘ └─────────────────────────┘ └────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ROW 4: DOMAIN TELEMETRY & MEASUREMENT INGESTION                                        │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────────────┐ │
│ │ Measurements/sec        │ │ Batch Size Histogram    │ │ Idempotency Conflicts / Min  │ │
│ │ Ingested by type        │ │ Payload size tracking   │ │ (Detects device retry storm) │ │
│ └─────────────────────────┘ └─────────────────────────┘ └────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ROW 5: CONTAINER & HOST RESOURCES                                                      │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌────────────────────────────┐ │
│ │ CPU Usage vs. Limit     │ │ Memory Usage vs. Limit  │ │ Container Restarts &         │ │
│ │ + CPU Throttling %      │ │ + OOM Kill events       │ │ Pod Status (Running/Pending) │ │
│ └─────────────────────────┘ └─────────────────────────┘ └────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ROW 6: CORRELATED LOGS & TRACE EXPLORER (Diagnostics)                                  │
│ ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Filtered Log Stream (status >= 500 or trace_id selected from exemplar point above) │ │
│ └────────────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Alerting Strategy: Priority Categorization & Routing

Alerts must be strictly prioritized so that on-call engineers are paged only for actionable problems.

### 6.1 Severity Levels

| Severity | Definition & Trigger Examples | Routing & Escalation |
|---|---|---|
| **P1 — Critical** | **Catastrophic Outage / Customer Impact**: <br>• Rapid SLO error budget depletion ($14.4\times$ burn rate). <br>• Database connection pool completely exhausted (`wait_queue > 5`). <br>• Synthetic canary test failing continuously. <br>• Service unresponsive (`/health` failing). | Immediate on-call escalation (high-urgency active page). Automatically escalates if unacknowledged. |
| **P2 — Major** | **Significant Degradation**: <br>• p99 Latency exceeds 1.5s for $> 5$ minutes. <br>• Moderate SLO budget drain ($6\times$ burn rate). <br>• Telemetry ingestion drops significantly below baseline (fleet network drop). <br>• Database active connections $> 85\%$ of server limit. <br>• Sustained surge or elevated rate of ERROR logs (detects silent failures in resilient fallbacks and background workers). | Urgent team notification (shared incident channel / alert feed). |
| **P3 — Warning** | **Non-Urgent Risk / Capacity Trend**: <br>• Storage volume free space $< 20\%$. <br>• Container CPU throttled for $> 15\%$ of cycles. <br>• Single pod restart loop detected. <br>• Elevated 4xx validation errors (client misconfiguration). | Asynchronous task tracking (issue tracker / low-priority alert feed). Triaged during standard working hours. |
| **P4 — Info** | **Operational Milestone**: <br>• Deployment completed. <br>• Database migration applied. <br>• Scheduled backup finished. | Audit log / deployment activity feed. No direct interruption. |

---

## 7. Summary Checklist for Implementation

1. **Structured Logs**: Update `app/infrastructure/logging.py` to output single-line JSON with `trace_id`, `span_id`, and `duration_ms`.
2. **Route Normalization**: Ensure metrics middleware captures parameterized templates (`/devices/{id}/measurements`) to protect against high-cardinality explosions.
3. **Database Instrumentation**: Expose `asyncpg` pool metrics (`active`, `idle`, `wait_queue_length`).
4. **Readiness Probe**: Implement `/health/ready` that verifies active DB pool connectivity with a fast timeout.
5. **Trace Correlation**: Inject trace IDs as exemplars into latency histograms to enable one-click root-cause analysis.
6. **Prioritized Alerts**: Configure P1/P2/P3 rules with grouping and mandatory runbook links before launching into production.
7. **Error Log Monitoring**: Export `log_messages_total` by level (or configure log aggregator metric filters) to alert on sustained error log spikes without relying solely on HTTP status codes.
