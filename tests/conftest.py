from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src import core
from src.app import models
from src.core.db import get_db_manager
from src.main import app

pytest_plugins = ["pytest_asyncio"]

db_manager = get_db_manager()


@pytest.fixture(scope="session")
async def setup_db_schema() -> AsyncGenerator[None]:
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(core.models.Base.metadata.create_all)
    yield
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(core.models.Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:  # noqa: ARG001
    async with db_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    app.dependency_overrides[db_manager.get_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> models.User:
    admin = models.User(
        name="Admin User",
        role=models.UserRole.ADMIN,
        api_key="key-" + str(uuid7()),
    )
    db_session.add(admin)
    await db_session.flush()
    return admin
