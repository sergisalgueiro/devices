# 006 — Business Rules Enforcement Summary

**Status:** Accepted  
**Date:** 2026-09-25

## Context

This document consolidates how each required business rule is enforced in the system, mapping each rule to the application-level logic, domain model, and database constraints that implement it.

## Rules and Enforcement

### 1. A device's serial number must be unique

| Layer | Mechanism |
|-------|-----------|
| Application | `CreateDeviceHandler` queries `get_by_serial_number()` before inserting; raises `SerialNumberAlreadyExistsError` (→ HTTP 409) if a match exists. |
| Database | `devices.serial_number` carries a `UNIQUE` constraint (migration `8b117ec1b50d`). A concurrent insert that passes the application check is still rejected by the DB. |

The application-level check provides a clean domain error message. The DB constraint is the definitive safety net against TOCTOU races under concurrent requests.

### 2. A device belongs to a single customer

| Layer | Mechanism |
|-------|-----------|
| Domain | `Device.customer_id` is typed `CustomerId | None` — a single optional value, not a collection. |
| Database | `devices.customer_id` is a single FK column referencing `customers.id`. There is no many-to-many join table. |
| Application | `Device.assign_customer()` rejects cross-customer re-assignment with `DeviceAlreadyAssignedError` (→ HTTP 409). Same-customer re-assignment (e.g. timezone update) remains idempotent. To transfer a device, callers must unassign first (`DELETE /devices/{id}/customer`), then assign to the new customer. `unassign_device_customer` sets `customer_id` to `NULL`. |

Ownership is structurally singular by design — the schema makes multi-customer assignment impossible.

### 3. Measurements can only be associated with existing devices

| Layer | Mechanism |
|-------|-----------|
| Application | `IngestMeasurementsHandler` fetches the device first; raises `DeviceNotFoundError` (→ HTTP 404) if it doesn't exist. |
| Database | `measurements.device_id` FK → `devices.id` with `ondelete=RESTRICT` (migration `9023476ba729`). The DB rejects any measurement pointing to a non-existent device. The RESTRICT also prevents deleting a device that still has measurements. |

### 4. Measurements cannot be ingested for inactive devices

| Layer | Mechanism |
|-------|-----------|
| Application | `IngestMeasurementsHandler` checks `device.is_active` after loading the device; raises `InactiveDeviceError` (→ HTTP 422) if the device is inactive. |
| Domain | `Device.is_active` is a plain boolean, defaulting to `True` on creation. The `set_active()` method toggles it. |

This rule is enforced only at the application level. No DB constraint prevents direct insertion of measurements for inactive devices — the check lives in the use-case handler. This is intentional: activation status is a business rule, not a referential integrity concern.

### 5. Idempotent measurement ingestion

| Layer | Mechanism |
|-------|-----------|
| API | The client provides a `measurement_id` (UUID) per measurement in the request body. |
| Repository | `save_batch()` uses PostgreSQL's `INSERT ... ON CONFLICT (id) DO NOTHING`. Duplicate IDs are silently skipped. |
| API response | Returns HTTP 201 regardless of whether all, some, or none of the measurements were new. The response is always successful if the device exists and is active. |

The client controls the idempotency key (`measurement_id`). Network retries that replay the same batch produce the same outcome with no duplicates.

### 6. Customer deletion: impact on devices and measurements

Documented in [ADR 005 — Customer Deletion: Devices and Measurements](005-customer-deletion-cascade.md).

**Summary of decisions:**

- **Customer record:** hard-deleted (row removed).
- **Devices:** orphaned — `customer_id` set to `NULL`; device record retained.
- **Measurements:** retained on the device, decoupled from customer lifecycle.
- **Mechanism:** the `devices.customer_id` FK uses `ondelete=RESTRICT`, meaning a customer with assigned devices cannot be deleted. The caller must explicitly unassign all devices first (`DELETE /devices/{id}/customer`), then delete the customer. This is a deliberate two-step process — no silent cascading.
- **Customer delete endpoint:** not yet implemented. The FK RESTRICT constraint is the current guardrail.

### 7. Concurrent modification of shared data

| Concern | Mechanism |
|---------|-----------|
| Transaction isolation | Every API mutation wraps its handler call in `async with db.begin()`, ensuring atomicity. PostgreSQL's default `READ COMMITTED` isolation applies. |
| Serial number races | Two concurrent `POST /devices` with the same serial number: the application check may pass for both, but the DB `UNIQUE` constraint rejects the second `INSERT`, producing a `409 Conflict`. |
| Email races | Same pattern as serial numbers: application pre-check + DB `UNIQUE` constraint on `customers.email`. |
| Measurement duplicates | `ON CONFLICT (id) DO NOTHING` makes concurrent ingestion of the same measurement ID safe — one wins, the rest are no-ops. |
| Device assignment / unassignment | `AssignDeviceCustomerHandler` and `UnassignDeviceCustomerHandler` fetch the device via `get_by_id_for_update`, which issues `SELECT … FOR UPDATE`. The row-level lock is held until the transaction commits, preventing concurrent assignment races: a second transaction blocks on the lock, re-reads the already-assigned device, and the domain check correctly rejects it. |
| Device activation / status | Concurrent activation toggles follow last-writer-wins semantics — no locking needed because `set_active()` is idempotent regardless of commit order. |

## Consequences

- All uniqueness rules have a DB-level backstop regardless of application logic.
- Referential integrity (measurements → devices → customers) is enforced by FK constraints with `RESTRICT`.
- Idempotency relies on client-provided IDs and PostgreSQL's `ON CONFLICT` mechanism.
- Customer deletion is a two-step manual process (unassign devices, then delete) — no automatic cascading.
- Assignment and unassignment operations use `SELECT FOR UPDATE` to guarantee read-then-write consistency. Idempotent operations (activation) remain last-writer-wins.
