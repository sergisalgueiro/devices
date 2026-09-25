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
