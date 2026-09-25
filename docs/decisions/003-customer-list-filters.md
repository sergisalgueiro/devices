# 003 — Customer List Filter Design

**Status:** Accepted  
**Date:** 2026-09-25

## Context

The `GET /customers` endpoint supports filtering the customer list. Decisions needed: which fields to filter on, what match strategy (exact vs. partial), and how multiple filters combine.

## Decision

Four optional query parameters:

| Parameter  | Match type                   | Notes                          |
|------------|------------------------------|--------------------------------|
| `email`    | Exact, case-sensitive        | Email is unique; at most one result |
| `country`  | Exact                        | ISO 3166-1 alpha-2 code (e.g., `ES`) |
| `language` | Exact                        | ISO 639-1 code (e.g., `en`) |
| `name`     | Case-insensitive partial (ILIKE) | Matches any substring |

Multiple filters combine with **AND** logic.

## Rationale

- Email uniqueness makes exact match the only sensible strategy.
- Country and language are controlled vocabularies (ISO codes) — exact match is correct and uses indexes efficiently.
- Name is free-text and users expect a search-like experience, so partial case-insensitive match (`ILIKE '%query%'`) is more useful.
- AND semantics are predictable and allow index usage on individual columns. OR queries would require full scans or more complex indexes with little practical benefit.

## Consequences

- Clients needing OR logic must issue multiple requests and merge results client-side.
- The `name` ILIKE filter cannot use a standard btree index efficiently; a GIN/trigram index can be added later if performance requires it.
