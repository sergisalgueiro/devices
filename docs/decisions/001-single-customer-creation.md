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

## Email Case Normalization

The `Email` value object normalizes all addresses to lowercase at construction time (`trimmed.lower()`).

**Why:** Per RFC 5321 §2.3.11 the domain part of an email address is explicitly case-insensitive. The local part is technically case-sensitive, but no major mail provider (Gmail, Outlook, Yahoo, ProtonMail, etc.) honours that distinction — they all treat `User` and `user` identically. The industry standard (Auth0, Stripe, AWS Cognito, Django, Rails) is to lowercase the full address before storage.

**Problem without normalization:** PostgreSQL `VARCHAR` / `TEXT` columns and their `UNIQUE` constraints are case-sensitive by default. Without lowercasing, `Alice@Example.com` and `alice@example.com` would be stored as two separate customers for the same person, and `WHERE email = 'alice@example.com'` would not find the first variant.

**Where it lives:** Normalization is performed in the `Email` value object (`app/domain/value_objects.py`), which is the single construction point for all email values entering the system. This guarantees every path — creation, lookup, filtering — uses a consistently lowercased email without requiring database-level changes (e.g. `CITEXT` or functional indexes).
