from collections.abc import Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models, schemas
from tests.conftest import AllBalances

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def get_orders(
    session: AsyncSession, order_type: models.order.OrderType, direction: models.order.Direction
) -> list[models.Order]:
    return list(
        (
            await session.scalars(
                select(models.Order).filter_by(
                    order_type=order_type,
                    direction=direction,
                )
            )
        ).all()
    )


@pytest.mark.parametrize(
    ("limit_direction", "market_direction", "expected_status", "qty_diff"),
    [
        (
            models.order.Direction.SELL,
            models.order.Direction.BUY,
            models.order.OrderStatus.EXECUTED,
            0,
        ),
        (
            models.order.Direction.SELL,
            models.order.Direction.BUY,
            models.order.OrderStatus.PARTIALLY_EXECUTED,
            4,
        ),
        (
            models.order.Direction.BUY,
            models.order.Direction.SELL,
            models.order.OrderStatus.EXECUTED,
            0,
        ),
        (
            models.order.Direction.BUY,
            models.order.Direction.SELL,
            models.order.OrderStatus.PARTIALLY_EXECUTED,
            4,
        ),
    ],
    ids=[
        "execute_one_limit_sell_order",
        "partially_execute_one_limit_sell_order",
        "execute_one_limit_buy_order",
        "partially_execute_one_limit_buy_order",
    ],
)
async def test_execute_limit_order_by_market_order(
    db_session: AsyncSession,
    user_client: AsyncClient,
    instrument: models.Instrument,
    admin_user: models.User,
    all_balances: AllBalances,
    create_order: Callable,
    limit_direction,
    market_direction,
    expected_status,
    qty_diff,
):
    start_user_balance, start_user_rub_balance, start_admin_balance, start_admin_rub_balance = [
        b.amount for b in all_balances
    ]

    limit_order_qty = 10
    trade_qty = limit_order_qty - qty_diff

    limit_order: models.Order = await create_order(
        direction=limit_direction,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=limit_order_qty,
        price=100,
        status=models.order.OrderStatus.NEW,
    )

    user_market_order_create = schemas.orders.Create(
        direction=market_direction,
        ticker=instrument.ticker,
        qty=trade_qty,
    )
    response = await user_client.post("/order", json=user_market_order_create.model_dump())
    assert "detail" not in response.json()

    market_orders = await get_orders(db_session, models.order.OrderType.MARKET, market_direction)
    limit_orders = await get_orders(db_session, models.order.OrderType.LIMIT, limit_direction)

    assert len(market_orders) == len(limit_orders) == 1

    market_order_db, limit_order_db = market_orders[0], limit_orders[0]

    assert limit_order_db.status == expected_status
    assert limit_order_db.filled == trade_qty

    if limit_direction == models.order.Direction.BUY:
        assert limit_order_db.locked_amount == (limit_order_qty * (limit_order.price or 0)) - (
            trade_qty * (limit_order.price or 0)
        )

    if limit_direction == models.order.Direction.SELL:
        assert limit_order_db.locked_amount == limit_order_qty - trade_qty

    assert market_order_db.status == models.order.OrderStatus.EXECUTED

    price = limit_order.price
    if market_direction == models.order.Direction.BUY:
        # Market BUY: user spends RUB, receives instrument; admin receives RUB, loses instrument
        assert all_balances.user_rub_balance.amount == start_user_rub_balance - trade_qty * price
        assert all_balances.admin_rub_balance.amount == start_admin_rub_balance + trade_qty * price
        assert all_balances.user_balance.amount == start_user_balance + trade_qty
        assert all_balances.admin_balance.amount == start_admin_balance - trade_qty
    else:
        # Market SELL: user receives RUB, loses instrument; admin spends RUB, receives instrument
        assert all_balances.user_rub_balance.amount == start_user_rub_balance + trade_qty * price
        assert all_balances.admin_rub_balance.amount == start_admin_rub_balance - trade_qty * price
        assert all_balances.user_balance.amount == start_user_balance - trade_qty
        assert all_balances.admin_balance.amount == start_admin_balance + trade_qty


@pytest.mark.parametrize(
    ("limit_direction", "market_direction"),
    [
        (
            models.order.Direction.SELL,
            models.order.Direction.BUY,
        ),
        (
            models.order.Direction.BUY,
            models.order.Direction.SELL,
        ),
    ],
    ids=[
        "insufficient_limit_sell_orders",
        "insufficient_limit_buy_orders",
    ],
)
async def test_market_fails_with_insufficient_limit_orders(
    db_session: AsyncSession,
    user_client: AsyncClient,
    instrument: models.Instrument,
    admin_user: models.User,
    create_order: Callable,
    all_balances: AllBalances,
    limit_direction,
    market_direction,
):
    limit_order: models.Order = await create_order(
        direction=limit_direction,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=10,
        price=10,
        status=models.order.OrderStatus.NEW,
    )

    trade_qty = limit_order.qty + 1

    market_order_create = schemas.orders.Create(
        direction=market_direction,
        ticker=instrument.ticker,
        qty=trade_qty,
    )
    response = await user_client.post("/order", json=market_order_create.model_dump())

    response_json = response.json()

    assert "detail" in response_json
    assert response_json["error_code"] == "market_order_not_filled"
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    ("qty_diff", "expected_order1_status", "expected_order2_status"),
    [
        (0, models.order.OrderStatus.EXECUTED, models.order.OrderStatus.EXECUTED),
        (2, models.order.OrderStatus.EXECUTED, models.order.OrderStatus.PARTIALLY_EXECUTED),
        (10, models.order.OrderStatus.EXECUTED, models.order.OrderStatus.NEW),
        (12, models.order.OrderStatus.PARTIALLY_EXECUTED, models.order.OrderStatus.NEW),
    ],
    ids=[
        "both_full_execution",
        "second_order_partial_execution",
        "first_executed_second_unchanged",
        "first_partially_executed_second_unchanged",
    ],
)
async def test_market_buy_executes_two_limit_sells(
    db_session: AsyncSession,
    user_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    create_order: Callable,
    all_balances: AllBalances,
    qty_diff,
    expected_order1_status,
    expected_order2_status,
):
    start_user_balance, start_user_rub_balance, start_admin_balance, start_admin_rub_balance = [
        b.amount for b in all_balances
    ]

    limit_order1 = await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=5,
        price=10,
        status=models.order.OrderStatus.NEW,
    )
    limit_order2 = await create_order(
        direction=models.order.Direction.SELL,
        instrument_id=instrument.id,
        user_id=admin_user.id,
        qty=10,
        price=20,
        status=models.order.OrderStatus.NEW,
    )

    total_qty = limit_order1.qty + limit_order2.qty
    trade_qty = total_qty - qty_diff

    market_order_create = schemas.orders.Create(
        direction=models.order.Direction.BUY,
        ticker=instrument.ticker,
        qty=trade_qty,
    )
    response = await user_client.post("/order", json=market_order_create.model_dump())
    assert "detail" not in response.json()

    assert (
        len(
            await get_orders(db_session, models.order.OrderType.MARKET, models.order.Direction.BUY)
        )
        == 1
    )

    limit_sell_orders_db = await get_orders(
        db_session, models.order.OrderType.LIMIT, models.order.Direction.SELL
    )
    assert len(limit_sell_orders_db) == 2  # noqa: PLR2004

    order1_db = await db_session.get(models.Order, limit_order1.id)
    assert order1_db is not None
    assert order1_db.status == expected_order1_status
    assert order1_db.filled == trade_qty if trade_qty <= order1_db.qty else order1_db.qty
    assert order1_db.locked_amount == order1_db.qty - (order1_db.filled or 0)

    order2_db = await db_session.get(models.Order, limit_order2.id)
    assert order2_db is not None
    assert order2_db.status == expected_order2_status
    assert order2_db.filled == 0 if trade_qty <= order1_db.qty else trade_qty - order1_db.qty
    assert order2_db.locked_amount == order2_db.qty - (order2_db.filled or 0)

    transferred_money = (order1_db.filled or 0) * (order1_db.price or 0) + (
        order2_db.filled or 0
    ) * (order2_db.price or 0)

    assert all_balances.user_rub_balance.amount == start_user_rub_balance - transferred_money
    assert all_balances.admin_rub_balance.amount == start_admin_rub_balance + transferred_money
    assert all_balances.user_balance.amount == start_user_balance + trade_qty
    assert all_balances.admin_balance.amount == start_admin_balance - trade_qty
