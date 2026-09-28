from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.infrastructure.db.settings import db_settings

# NullPool: this app runs locally only, so per-query connection overhead is negligible.
engine = create_async_engine(db_settings.database_url, echo=False, poolclass=NullPool)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session per request.

    Opens a single transaction for the entire request lifetime: commits on
    success and rolls back automatically on any exception, regardless of
    whether the endpoint is a read or a write.
    """
    async with AsyncSessionFactory() as session:
        async with session.begin():
            yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
