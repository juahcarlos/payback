from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


def create_session(bind: AsyncConnection | None = None) -> AsyncSession:
    if bind is None:
        return session_factory()
    return session_factory(bind=bind)
