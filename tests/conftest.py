from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src import core
from src.app import models, schemas
from src.app.api.v1 import dependencies
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
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:
    async with db_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def anonim_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """
    Yields:
        AsyncClient: Non-authenticated client
    """
    app.dependency_overrides[db_manager.get_session] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def user_client(anonim_client: AsyncClient, user: models.User) -> AsyncClient:
    app.dependency_overrides[dependencies.get_current_user] = (
        lambda: schemas.UserRead.model_validate(user)
    )
    return anonim_client


@pytest.fixture(scope="function")
def admin_client(anonim_client: AsyncClient, admin_user: models.User) -> AsyncClient:
    app.dependency_overrides[dependencies.get_current_user] = (
        lambda: schemas.UserRead.model_validate(admin_user)
    )
    return anonim_client


@pytest.fixture(scope="function")
async def user(db_session: AsyncSession) -> models.User:
    user = models.User(
        name="User",
        role=models.UserRole.USER,
        api_key="key-" + str(uuid7()),
    )
    db_session.add(user)
    await db_session.flush()
    return user


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
