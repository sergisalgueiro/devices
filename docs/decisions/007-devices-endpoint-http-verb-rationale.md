# 007 — HTTP Verb Rationale for Devices Endpoints

**Status:** Accepted  
**Date:** 2026-09-26

## Context

The devices API exposes two sub-resource endpoints whose HTTP verbs may not be immediately obvious:

- `DELETE /devices/{id}/customer` — removes the customer assignment.
- `PATCH /devices/{id}/activation` — toggles the activation state.

Both use sub-resource URLs, but they use different verbs. The reasoning behind each choice is documented here to prevent future inconsistency.

## Decision

### `DELETE /devices/{id}/customer` for unassignment

The URL `/{device_id}/customer` represents the **assignment relationship** as a sub-resource. The full set of verbs for this sub-resource is:

| Verb | Endpoint | Meaning |
|------|----------|---------|
| `PUT` | `/devices/{id}/customer` | Create or replace the assignment |
| `DELETE` | `/devices/{id}/customer` | Destroy the assignment |

`DELETE` is correct here because the assignment either **exists or does not exist**. Unassigning a device removes the relationship resource entirely — there is nothing left to represent once it is gone.

RPC-style alternatives (`POST /devices/{id}/unassign`) were rejected as they model actions rather than resources and are less idiomatic REST.

### `PATCH /devices/{id}/activation` for toggling activation

Activation is a **persistent attribute** of the device, not a relationship. The sub-resource `/activation` always exists — it cannot be destroyed, only updated. Using `DELETE` to deactivate would be semantically wrong: it would imply the concept of activation disappears from the device, which is not the case.

`PATCH` models a partial update of a persistent sub-resource, which is the correct fit when the goal is to transition between two states (`active` / `inactive`).

## Rationale

The key distinction is:

- **Relationship existence** (assignment) → `PUT` to create, `DELETE` to destroy.
- **Persistent attribute state** (activation) → `PATCH` to update in place.

Both endpoints treat their URL segment as a sub-resource consistently. The verb differs because the underlying semantic differs.

## Consequences

- `DELETE /devices/{id}/customer` returns `204 No Content` — the sub-resource no longer exists.
- `PATCH /devices/{id}/activation` returns `204 No Content` — the sub-resource was updated but there is nothing new to return.
- Both operations are idempotent: repeated calls with the same intent always succeed.
