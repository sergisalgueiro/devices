# 002 — Cursor-Based Pagination

**Status:** Accepted  
**Date:** 2026-09-25

## Context

The `GET /customers` endpoint lists customers and needs a pagination strategy. The two common approaches are offset/limit and cursor-based (keyset) pagination.

## Decision

Use cursor-based (keyset) pagination. The response includes an opaque `next_cursor` string and a `has_more` flag. To fetch the next page, the client passes `cursor=<next_cursor>` in the next request.

The cursor is a base64-encoded JSON blob containing the sort field, sort direction, last-seen sort value, and last-seen row ID. This makes it self-contained and resistant to sort context mismatches between pages.

## Rationale

- **O(1) performance at any depth**: offset pagination requires the database to count and skip rows, which degrades on large tables. Keyset pagination always uses an indexed range condition.
- **Stable results**: offset pagination shifts when rows are inserted or deleted between pages (users see duplicates or miss rows). Keyset pagination is immune to concurrent writes.
- **Tradeoff**: no random page access ("jump to page 47"). This is acceptable for a UI table with next/previous navigation.

## Consequences

- Clients must store and forward the cursor; they cannot jump to arbitrary pages.
- The cursor is opaque — clients must not parse or construct cursors manually.
- Default sort is `created_at asc`; supported fields: `created_at`, `name`, `email`.

## Indexes

Cursor pagination is only O(1) if the sort columns are indexed. Every keyset range condition takes the form:

```sql
WHERE device_id = :id AND (timestamp, id) > (:last_ts, :last_id)
ORDER BY timestamp, id
LIMIT :n
```

A **composite index on `(device_id, timestamp, id)`** serves this pattern in a single index seek — no filesort. The leading `device_id` column satisfies the equality filter; `timestamp` and `id` provide the pre-sorted order the seek needs. Because any equality prefix of a composite index also covers point-lookups by `device_id` alone, the old single-column `ix_measurements_device_id` index is fully subsumed and was removed (migration `b3c4d5e6f7a8`).

The same principle applies to customers: `ix_customers_created_at_id`, `ix_customers_name_id`, and `ix_customers_email_id` were added in migration `f1e2d3c4b5a6` for the same reason — each covers one sortable field plus `id` as a tiebreaker.
