from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import AsyncSessionFactory, get_db
from app.main import app


@pytest.fixture(autouse=True)
async def db_session():
    async with AsyncSessionFactory() as session:
        await session.begin()
        # Redirect all begin() calls to begin_nested() so endpoints "commit"
        # SAVEPOINTs without touching the outer transaction we roll back here.
        session.begin = session.begin_nested

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        yield session
        await session.rollback()
    app.dependency_overrides.pop(get_db, None)
