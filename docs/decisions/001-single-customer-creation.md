# 001 — Single Customer Creation

**Status:** Accepted  
**Date:** 2026-09-25

## Context

The customer management API needs a creation endpoint. The question is whether to support creating one customer per request or batching multiple customers in a single call.

## Decision

`POST /customers` accepts a single customer and creates exactly one. No batch endpoint exists.

## Rationale

Customers are created through self-registration — a human filling in their own details. This is inherently a one-at-a-time interaction. Batch creation would add complexity in error handling (partial success, per-item error reporting) with no real-world use case to justify it.

## Consequences

- Callers that need to create many customers must call the endpoint once per customer.
- Error handling is straightforward: one request, one outcome (201, 409, or 422).

## Concurrency & Duplicate Handling

Under concurrent requests both transactions can pass the application-level uniqueness check before either writes. The database unique constraint on `email` catches the duplicate. The repository catches `psycopg.errors.UniqueViolation` (pg error `23505`) and re-raises it as `CustomerEmailAlreadyExistsError`, which the exception handler maps to 409. A broader `IntegrityError` is not caught — only the specific unique-violation subclass is handled, so other constraint failures still surface as unexpected errors.
