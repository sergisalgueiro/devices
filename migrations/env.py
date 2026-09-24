import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Inject DATABASE_URL from environment, overriding the blank alembic.ini value
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Set up loggers from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import ALL ORM models so Alembic can detect them for autogenerate
# ---------------------------------------------------------------------------
from app.infrastructure.db.models.base import Base  # noqa: E402
import app.infrastructure.db.models.customer  # noqa: E402, F401
import app.infrastructure.db.models.device  # noqa: E402, F401
import app.infrastructure.db.models.measurement  # noqa: E402, F401

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode (no live DB connection needed — emits SQL to stdout)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode (async engine)
# ---------------------------------------------------------------------------
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async SQLAlchemy engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
