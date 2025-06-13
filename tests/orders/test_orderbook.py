from collections.abc import Callable

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models
from tests.conftest import AllBalances

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_orderbook_one_ask(
    db_session: AsyncSession,
    user_client: AsyncClient,
    instrument: models.Instrument,
    admin_user: models.User,
    create_order: Callable,
    all_balances: AllBalances,
):
    limit_order: models.Order = await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=1,
        price=100,
        status=models.order.OrderStatus.NEW,
    )

    response = await user_client.get(f"/public/orderbook/{instrument.ticker}")
    response_json = response.json()

    assert "ask_levels" in response_json
    assert "bid_levels" in response_json

    assert len(response_json["ask_levels"]) == 1
    assert len(response_json["bid_levels"]) == 0

    assert response_json["ask_levels"][0]["price"] == limit_order.price
    assert response_json["ask_levels"][0]["qty"] == limit_order.qty


async def test_orderbook_same_price_asks(
    db_session: AsyncSession,
    user_client: AsyncClient,
    instrument: models.Instrument,
    admin_user: models.User,
    create_order: Callable,
    all_balances: AllBalances,
):
    limit_order1: models.Order = await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=10,
        price=100,
        status=models.order.OrderStatus.NEW,
    )

    limit_order2: models.Order = await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=15,
        price=100,
        status=models.order.OrderStatus.NEW,
    )

    response = await user_client.get(f"/public/orderbook/{instrument.ticker}")
    response_json = response.json()

    assert "ask_levels" in response_json
    assert "bid_levels" in response_json

    assert len(response_json["ask_levels"]) == 1
    assert len(response_json["bid_levels"]) == 0

    assert response_json["ask_levels"][0]["price"] == limit_order1.price == limit_order2.price
    assert response_json["ask_levels"][0]["qty"] == limit_order1.qty + limit_order2.qty


async def test_only_limit_in_orderbook(
    db_session: AsyncSession,
    user_client: AsyncClient,
    instrument: models.Instrument,
    admin_user: models.User,
    create_order: Callable,
    all_balances: AllBalances,
):
    await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=10,
        price=100,
        status=models.order.OrderStatus.NEW,
    )

    await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=5,
        status=models.order.OrderStatus.NEW,
    )

    response = await user_client.get(f"/public/orderbook/{instrument.ticker}")
    response_json = response.json()

    assert "ask_levels" in response_json
    assert "bid_levels" in response_json

    assert len(response_json["ask_levels"]) == 1
    assert len(response_json["bid_levels"]) == 0
