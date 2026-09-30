# 009 — Forward-Only Database Migrations

**Status:** Accepted  
**Date:** 2026-09-30

## Context

Database migration frameworks (such as Alembic) generate bidirectional migration scripts containing both `upgrade()` and `downgrade()` functions. While running `downgrade()` can be convenient during local development, executing database downgrades in production or automated deployment pipelines (CI/CD) introduces severe operational and data integrity hazards:

1. **Destructive Data Loss**: Downward migrations (e.g. `DROP TABLE`, `DROP COLUMN`) permanently wipe data written by application traffic while the schema was live.
2. **State Inconsistency & Infeasible Reversals**: Migrations that weaken constraints (e.g. making `customer_id` nullable) cannot be cleanly downgraded once live rows with null values have been committed. Reverting constraints (`SET NOT NULL`) crashes immediately with constraint violations.
3. **Silent State Drift (Split-Brain)**: If a downgrade is stubbed out with `pass` or log-only statements, Alembic's version tracking table (`alembic_version`) rolls back to the previous revision while the physical database schema remains on the new version. Subsequent `upgrade head` commands crash attempting to re-create existing tables or columns.
4. **Zero-Downtime & Rolling Deployment Failures**: Modern deployments operate across multiple instances/containers. Downgrading the database while new application replicas are serving traffic or before old replicas terminate immediately causes 500 errors.
5. **Untested Execution Paths**: Unlike `upgrade()` which is exercised continuously in CI and testing, `downgrade()` routines are rarely tested against realistic data volumes or concurrent connections.
6. **Automated Rollback Risks in CI/CD**: Naive CI/CD pipelines or incident response scripts that trigger `alembic downgrade -1` upon deployment failure risk turning an application bug into irreversible data corruption.

## Decision

Adopt a **strict forward-only database migration policy** across all environments.

1. **Explicit Prohibition of Downgrades**: All `downgrade()` functions across all Alembic migration scripts must raise `NotImplementedError`, refusing to execute.
2. **Template Enforcement**: The migration generation template (`migrations/script.py.mako`) is configured to generate `raise NotImplementedError` by default in `downgrade()`.
3. **Forward-Only Remediation ("Roll Forward")**: Any fix, schema adjustment, or rollback of a previous change must be implemented as a **new forward migration** (e.g. an explicit compensating transaction or corrective DDL) applied via `alembic upgrade head`.
4. **Removal of Local Rollback Commands**: The `make rollback` command is retired from standard workflows. Reverting local developer environments requires rebuilding the local container/database volume rather than rewinding schema state.

## Rationale

- **Guaranteed Synchronization**: Raising an unhandled exception (`NotImplementedError`) aborts the migration transaction without updating `alembic_version`. The database schema and tracking metadata remain completely synchronized.
- **Fail-Safe Pipeline Protection**: Even if a developer, CI/CD pipeline, or deployment script accidentally triggers `alembic downgrade`, the operation immediately halts with an exit code of 1 before executing any DDL or destroying data.
- **Expand/Contract Compatibility**: Decoupling database evolution from application rollbacks encourages the expand/contract pattern, where database changes are made backward-compatible with the previous application release.
- **Clear Disaster Recovery Boundaries**: Catastrophic database incidents are handled via Point-in-Time Recovery (PITR) from backups and WAL archives, never through fragile in-place DDL downgrades.

## Consequences

- Any execution of `alembic downgrade` will raise `NotImplementedError` and fail immediately.
- Schema adjustments must always be authored as new revisions moving forward in the migration graph.
- Developers iterating locally on uncommitted migrations who wish to discard schema changes must reset their local Docker database volume (`docker compose down -v && docker compose up -d && make migrate`).
