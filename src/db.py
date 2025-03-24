from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings


class DatabaseManager:
    def __init__(self):
        """
        Initialize a DatabaseManager instance.
        
        Retrieves configuration settings, creates an asynchronous database engine, and sets up a session factory for managing database sessions.
        """
        self.settings = get_settings()
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    def _create_engine(self) -> AsyncEngine:
        """
        Creates and returns an asynchronous SQLAlchemy engine.
        
        The engine is configured based on instance settings. It converts the configured
        database URL to a string, enables echo mode when debugging is active, and selects the
        connection pool class depending on the debug mode. In debugging, it uses a NullPool
        (with no connection pooling) and disables connection recycling (value -1); otherwise,
        it uses an AsyncAdaptedQueuePool with a recycle period of 900 seconds.
        
        Returns:
            AsyncEngine: A configured asynchronous SQLAlchemy engine.
        """
        return create_async_engine(
            str(self.settings.DATABASE_URL),
            echo=self.settings.DEBUG,
            poolclass=NullPool if self.settings.DEBUG else AsyncAdaptedQueuePool,
            pool_recycle=900 if not self.settings.DEBUG else -1,
        )

    def _create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Creates an asynchronous session factory for managing database sessions.
        
        The factory is bound to the current engine and configured to create AsyncSession
        instances with commit expiration disabled.
        """
        return async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Asynchronously yield a database session with automatic transaction management.
        
        Retrieves a session from the session factory within a transaction context.
        The session is available for database operations and is automatically closed
        after completing the context.
        """
        async with self.session_factory.begin() as session:
            yield session

    # for manual testing
    @asynccontextmanager
    async def session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides an asynchronous context manager for acquiring a database session.
        
        Yields an AsyncSession instance that is automatically managed within the context.
        The session is begun when entering the context and properly closed upon exit,
        making it ideal for controlled session usage and manual testing.
        """
        async with self.session_factory.begin() as session:
            yield session


db_manager = DatabaseManager()
