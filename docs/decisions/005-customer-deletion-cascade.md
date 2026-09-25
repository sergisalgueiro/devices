# 005 — Customer Deletion: Devices and Measurements

**Status:** Accepted  
**Date:** 2026-09-25

## Context

When a customer is deleted, the system must decide what happens to their associated devices and the measurements recorded by those devices.

## Decision

- **Customer record**: hard delete — the customer row is permanently removed.
- **Devices**: orphaned — `customer_id` is set to `NULL`; the device record is retained.
- **Measurements**: retained indefinitely on the device, decoupled from the customer lifecycle.

## Rationale

Measurements are telemetry tied to the device, not to the customer. Retaining them on the device after a customer is deleted preserves a historical baseline useful for diagnostics — for example, comparing current sensor readings against past behaviour to detect malfunction or degradation.

Hard delete is preferred over soft delete for the customer record because:

1. The "customer recovery" use case doesn't justify it — a returning customer would re-register rather than restore old state.
2. Soft delete keeps PII (name, email, contact info) in the database indefinitely, working against data minimisation obligations.

> **Legal note**: depending on jurisdiction and applicable regulation (e.g. GDPR right to erasure), customers may have the right to request deletion of all data associated with them, including measurements. Retention limits for measurement data are therefore not purely a business decision — they may be legally constrained. The specific retention period should be defined in coordination with legal and, where applicable, linked to the customer's subscription tier.

Device transfer between customers (what should happen to measurements when a device moves from one customer to another) is out of scope for this project; there is no authentication layer to enforce per-customer data isolation.

## Consequences

- Deleting a customer does not cascade to devices or measurements.
- Devices whose customer has been deleted become unassigned (`customer_id = NULL`) and available for reassignment.
- Customer PII is removed on deletion; measurement data survives on the device.
- A future data retention policy (driven by business rules, subscription tier, or legal requirements) must handle measurement cleanup independently of customer lifecycle.
