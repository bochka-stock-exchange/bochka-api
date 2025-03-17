from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config import get_settings

settings = get_settings()


def create_db_engine() -> AsyncEngine:
    return create_async_engine(
        str(settings.DATABASE_URL),
        echo=False,
        poolclass=NullPool if settings.DEBUG else AsyncAdaptedQueuePool,
        future=True,
    )


engine = create_db_engine()

async_session_factory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_transaction_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        async with session.begin():
            yield session
