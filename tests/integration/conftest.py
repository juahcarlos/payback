import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.core.database as database


@pytest.fixture
async def unpooled_test_database(monkeypatch: pytest.MonkeyPatch, anyio_backend: str):
    test_engine = create_async_engine(
        database.settings.database_url,
        poolclass=NullPool,
    )
    monkeypatch.setattr(
        database,
        "session_factory",
        async_sessionmaker(test_engine, expire_on_commit=False),
    )
    try:
        yield
    finally:
        await test_engine.dispose()
