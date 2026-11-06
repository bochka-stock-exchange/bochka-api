from collections.abc import AsyncGenerator, Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pydantic import validate_call
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import src.app
from src import core
from src.app import models, schemas
from src.app.api import dependencies
from src.core.uow import UnitOfWork
from src.main import app

postgres_manager = core.db.get_postgres_manager()

SQLModelType = TypeVar("SQLModelType", bound=core.models.sqlalchemy.Base)


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

    monkeypatch.setattr(UnitOfWork, "__aenter__", patched_aenter)
    monkeypatch.setattr(UnitOfWork, "__aexit__", patched_aexit)


@pytest.fixture(scope="function")
async def client(mock_uow: None) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1",
    ) as client:
        yield client

    app.dependency_overrides = {}


async def create_in_db[SQLModelType](session: AsyncSession, entity: SQLModelType) -> SQLModelType:
    session.add(entity)
    await session.flush()
    await session.refresh(entity)
    return entity


@pytest.fixture(scope="function")
async def user(db_session: AsyncSession) -> models.User:
    return await create_in_db(db_session, models.User(name="User", role=models.UserRole.USER))


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> models.User:
    return await create_in_db(
        db_session,
        models.User(name="Admin User", role=models.UserRole.ADMIN),
    )


@pytest.fixture(scope="function")
async def instrument(db_session: AsyncSession) -> models.Instrument:
    return await create_in_db(db_session, models.Instrument(ticker="BB", name="Bobrito Bandito"))


@pytest.fixture(scope="function")
async def rub_instrument(db_session: AsyncSession) -> models.Instrument:
    return await create_in_db(db_session, models.Instrument(ticker="RUB", name="Rubles"))


@pytest.fixture(scope="function")
async def admin_balance(
    db_session: AsyncSession,
    admin_user: models.User,
    instrument: models.Instrument,
) -> models.Balance:
    return await create_in_db(
        db_session,
        models.Balance(user_id=admin_user.id, instrument_id=instrument.id, amount=1000),
    )


@pytest.fixture(scope="function")
async def admin_rub_balance(
    db_session: AsyncSession,
    admin_user: models.User,
    rub_instrument: models.Instrument,
) -> models.Balance:
    return await create_in_db(
        db_session,
        models.Balance(user_id=admin_user.id, instrument_id=rub_instrument.id, amount=1000),
    )


@pytest.fixture(scope="function")
async def user_balance(
    db_session: AsyncSession,
    user: models.User,
    instrument: models.Instrument,
) -> models.Balance:
    return await create_in_db(
        db_session,
        models.Balance(user_id=user.id, instrument_id=instrument.id, amount=1000),
    )


@pytest.fixture(scope="function")
async def user_rub_balance(
    db_session: AsyncSession,
    user: models.User,
    rub_instrument: models.Instrument,
) -> models.Balance:
    return await create_in_db(
        db_session,
        models.Balance(user_id=user.id, instrument_id=rub_instrument.id, amount=1000),
    )


@dataclass
class AllBalances:
    user_balance: models.Balance
    user_rub_balance: models.Balance
    admin_balance: models.Balance
    admin_rub_balance: models.Balance

    def __iter__(self) -> Iterator[models.Balance]:
        yield self.user_balance
        yield self.user_rub_balance
        yield self.admin_balance
        yield self.admin_rub_balance


@pytest.fixture(scope="function")
def all_balances(
    user_balance: models.Balance,
    user_rub_balance: models.Balance,
    admin_balance: models.Balance,
    admin_rub_balance: models.Balance,
) -> AllBalances:
    return AllBalances(
        user_balance=user_balance,
        user_rub_balance=user_rub_balance,
        admin_balance=admin_balance,
        admin_rub_balance=admin_rub_balance,
    )


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
def create_order(db_session: AsyncSession, rub_instrument: models.Instrument) -> Callable:
    @validate_call
    async def _create_order(
        user_id: UUID,
        instrument_id: UUID,
        status: models.order.OrderStatus,
        direction: models.order.Direction,
        qty: schemas.orders.OrderQuantity,
        price: schemas.orders.LimitOrderPrice | None = None,
    ) -> models.Order:
        params = dict(locals())

        params.pop("db_session", None)
        params.pop("rub_instrument", None)

        is_buy, is_sell = (
            direction == models.order.Direction.BUY,
            direction == models.order.Direction.SELL,
        )
        is_limit = price is not None

        order = models.Order(
            **params,
            locked_money_amount=qty * price if is_buy and price else None,
            locked_instrument_amount=qty if is_sell and price else None,
            order_type=models.order.OrderType.LIMIT if is_limit else models.order.OrderType.MARKET,
            filled=0 if is_limit else None,
        )
        return await create_in_db(db_session, order)

    return _create_order
