# 004 — Device Creation Decoupled from Customer Assignment

**Status:** Accepted  
**Date:** 2026-09-25  
**Updated:** 2026-09-28

## Context

The original design required a `customer_id` at device creation time. In practice, devices are manufactured and registered independently of any customer — they are warehoused, shipped, and only later activated by a customer. Customers can also return or resell devices, so ownership must be mutable. Tying creation to assignment made these workflows impossible.

## Decision

Device creation (`POST /devices`) takes only a `serial_number`. Customer assignment is a separate, explicit operation:

- `PUT /devices/{id}/customer` — assign a device to a customer, optionally setting a timezone.
- `DELETE /devices/{id}/customer` — unassign a device from its customer.

## Rationale

### Device identity is independent of ownership

A serial number identifies a physical unit. That identity exists before any customer ever touches it. Conflating "register this hardware" with "assign it to a customer" was a domain modelling error.

### Timezone belongs to the deployment context, not the device

A device's timezone reflects where the customer operates it, not a property of the hardware itself. It is therefore set at assignment time and cleared on unassignment. This keeps the device entity clean and avoids stale timezone data after ownership changes.

### Nullable `customer_id` with SET NULL on delete

`customer_id` is nullable in the database. The FK uses `ondelete=SET NULL` — deleting a customer automatically nulls out `customer_id` on all devices they owned, orphaning them back to the unassigned pool.

This was preferred over `RESTRICT` (which blocked customer deletion until devices were manually unassigned) because:

- "Unassigned" is already a first-class, valid device state — devices start life unassigned.
- Deleting a customer is the deliberate act; automatically releasing their devices is the natural consequence, not a hidden side-effect.
- `RESTRICT` shifted operational burden to callers, who would need to discover, loop through, and unassign all owned devices before every customer deletion.
- No data is lost: measurements belong to the device, not the customer.

`SET NULL` was preferred over removing the FK entirely because the FK still guarantees referential integrity — no device can reference a non-existent customer row — while giving callers the simpler delete-and-done workflow.

### Assign is idempotent; unassign is a no-op when already unassigned

Re-assigning to the same or a different customer always succeeds (no conflict error). Unassigning an already-unassigned device returns 204 without error. Both choices reduce friction for callers that cannot guarantee prior state.

## Consequences

- `POST /devices` no longer accepts `customer_id` or `timezone`.
- `DeviceResponse.customer_id` and `timezone` can be `null`.
- Clients that previously created devices pre-assigned must call `PUT /devices/{id}/customer` as a second step.
- Deleting a customer automatically orphans all their devices (sets `customer_id = NULL`). No pre-unassignment step is required.
