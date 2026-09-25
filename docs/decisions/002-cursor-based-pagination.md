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
