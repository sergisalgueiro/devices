# 004 — Device Creation Decoupled from Customer Assignment

**Status:** Accepted  
**Date:** 2026-09-25

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

### Nullable `customer_id` with RESTRICT on delete

`customer_id` is nullable in the database. The FK still uses `ondelete=RESTRICT` — deleting a customer while they own devices is blocked. Unassignment must be explicit. This prevents accidental orphaning of devices and makes ownership changes a deliberate act.

### Assign is idempotent; unassign is a no-op when already unassigned

Re-assigning to the same or a different customer always succeeds (no conflict error). Unassigning an already-unassigned device returns 204 without error. Both choices reduce friction for callers that cannot guarantee prior state.

## Consequences

- `POST /devices` no longer accepts `customer_id` or `timezone`.
- `DeviceResponse.customer_id` and `timezone` can be `null`.
- Clients that previously created devices pre-assigned must call `PUT /devices/{id}/customer` as a second step.
- Deleting a customer who still owns devices will return a database-level error (FK RESTRICT). The caller must unassign devices first.
