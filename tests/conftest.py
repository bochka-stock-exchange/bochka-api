from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import src.app
from src import core
from src.app import models, schemas
from src.app.api import dependencies
from src.main import app

postgres_manager = core.db.get_postgres_manager()


@pytest.fixture(scope="session", autouse=True)
def app_client():
    with TestClient(src.app.create_app()):
        yield


@pytest.fixture(scope="session")
async def setup_db_schema() -> None:
    async with postgres_manager.engine.begin() as conn:
        await conn.run_sync(core.models.sqlalchemy.Base.metadata.create_all)

        if tables := core.models.sqlalchemy.Base.metadata.tables.values():
            table_names = ",".join(f'"{table.name}"' for table in tables)
            await conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE;"))


@pytest.fixture(scope="function")
async def db_session(setup_db_schema) -> AsyncGenerator[AsyncSession]:
    async with postgres_manager.session_factory.begin() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="function")
async def mock_uow(monkeypatch: pytest.MonkeyPatch, db_session: AsyncSession) -> None:  # noqa: RUF029
    async def patched_aenter(self):  # noqa: RUF029
        self._postgres_session = db_session
        return self

    async def patched_aexit(*args, **kwargs):
        pass

    monkeypatch.setattr(core.UnitOfWork, "__aenter__", patched_aenter)
    monkeypatch.setattr(core.UnitOfWork, "__aexit__", patched_aexit)


@pytest.fixture(scope="function")
async def client(mock_uow: None) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def user(db_session: AsyncSession) -> models.User:
    user = models.User(
        name="User",
        role=models.UserRole.USER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> models.User:
    admin = models.User(
        name="Admin User",
        role=models.UserRole.ADMIN,
    )
    db_session.add(admin)
    await db_session.flush()
    await db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def user_client(client: AsyncClient, user: models.User) -> AsyncClient:
    app.dependency_overrides[dependencies.permissions.get_current_user] = (
        lambda: schemas.users.Read.model_validate(user)
    )
    return client


@pytest.fixture(scope="function")
def admin_client(client: AsyncClient, admin_user: models.User) -> AsyncClient:
    app.dependency_overrides[dependencies.permissions.get_current_user] = (
        lambda: schemas.users.Read.model_validate(admin_user)
    )
    return client


@pytest.fixture(scope="function")
async def instrument(db_session: AsyncSession) -> models.Instrument:
    instrument = models.Instrument(
        ticker="BB",
        name="Bobrito Bandito",
    )
    db_session.add(instrument)
    await db_session.flush()
    await db_session.refresh(instrument)
    return instrument


@pytest.fixture(scope="function")
async def balance(
    db_session: AsyncSession, admin_user: models.User, instrument: models.Instrument
) -> models.Balance:
    balance = models.Balance(
        user_id=admin_user.id,
        instrument_id=instrument.id,
        amount=1000,
    )
    db_session.add(balance)
    await db_session.flush()
    await db_session.refresh(balance)
    return balance
