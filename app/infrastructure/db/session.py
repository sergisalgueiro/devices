from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db.settings import db_settings

engine = create_async_engine(db_settings.database_url, echo=False)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session per request."""
    async with AsyncSessionFactory() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
