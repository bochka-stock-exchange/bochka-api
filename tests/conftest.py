from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src.db import db_manager
from src.main import app
from src.models.base import Base
from src.models.user import User, UserRole

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
async def setup_db_schema() -> AsyncGenerator[None, None]:
    """
    Set up and tear down the database schema for testing.
    
    Creates all tables defined in the SQLAlchemy metadata before tests run and drops them afterward,
    ensuring a clean test environment.
    """
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous SQLAlchemy session for use in tests.
    
    This fixture initiates a database session using the session factory and yields
    an active session for database operations. After the test completes, it
    automatically rolls back any uncommitted changes to maintain isolation.
        
    Yields:
        AsyncSession: An active session for interacting with the database.
    """
    async with db_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an asynchronous HTTP client for testing API endpoints.
    
    Overrides the application's database session dependency with the provided AsyncSession,
    creates an AsyncClient with an ASGITransport configured for the FastAPI app, and resets
    the dependency overrides after use.
    """
    app.dependency_overrides[db_manager.get_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api/v1"
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """
    Creates an admin user for testing.
    
    Constructs a new User instance with the admin role, a default name, and a unique API key.
    The user is added to the asynchronous database session and the session is flushed to persist
    the user, which is then returned for use in tests.
    
    Returns:
        User: The created admin user instance.
    """
    admin = User(name="Admin User", role=UserRole.ADMIN, api_key="key-" + str(uuid7()))
    db_session.add(admin)
    await db_session.flush()
    return admin
