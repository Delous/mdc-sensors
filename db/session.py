from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url_async,
    echo=False,
    pool_pre_ping=True,
)

SessionMaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionMaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


session_context = asynccontextmanager(get_session)


async def close_db_engine() -> None:
    await engine.dispose()
