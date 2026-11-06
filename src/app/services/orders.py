from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src import core
from src.app import models, repositories, schemas, services, utils

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Orders(
    core.services.BaseCRUD[
        schemas.orders.Create,
        schemas.orders.Read,
        schemas.orders.Update,
        schemas.orders.Filters,
        schemas.orders.SortParams,
        models.Order,
    ],
):
    def __init__(self):
        self.repo = repositories.Orders()
        super().__init__(
            self.repo,
            create_schema=schemas.orders.Create,
            read_schema=schemas.orders.Read,
            update_schema=schemas.orders.Update,
            filters_schema=schemas.orders.Filters,
        )

    async def find_active_limit_orders(
        self,
        uow: UnitOfWork,
        instrument_id: UUID,
        pagination: core.schemas.PaginationParams | None = None,
    ) -> list[schemas.orders.Read]:
        all_orders = await self.read_many(
            uow,
            filters=schemas.orders.Filters(
                instrument_id=instrument_id,
                order_type=models.order.OrderType.LIMIT,
                status=[models.order.OrderStatus.NEW, models.order.OrderStatus.PARTIALLY_EXECUTED],
            ),
            pagination=pagination,
        )
        return all_orders

    async def create(
        self,
        uow: UnitOfWork,
        create_schema: schemas.orders.Create,
        *,
        additional_data: dict[str, Any] | None = None,
    ) -> schemas.orders.Read:
        self.instrument_service = services.Instruments()
        self.balance_service = services.Balances()

        rub_instrument = await self.instrument_service.read_by_ticker(uow, "RUB")

        rub_balance = await self.balance_service.get_or_create_user_balance(
            uow,
            create_schema.user_id,
            rub_instrument.id,
        )
        instrument_balance = await self.balance_service.get_or_create_user_balance(
            uow,
            create_schema.user_id,
            create_schema.instrument_id,
        )

        additional_data = await self._get_locked_amounts(
            uow,
            create_schema,
            rub_balance,
            instrument_balance,
        )
        async with uow.postgres_session.begin_nested():
            with threading.Lock():
                order = await super().create(uow, create_schema, additional_data=additional_data)

        order_book_manager = utils.get_order_book_manager()

        if create_schema.order_type == models.order.OrderType.LIMIT:
            order_book = await order_book_manager.get_order_book(
                uow,
                create_schema.instrument_id,
                core.schemas.PaginationParams(limit=100),
                refresh=True,
            )

            if create_schema.direction == models.order.Direction.BUY:  # BUY LIMIT order
                best_ask_order = order_book.asks[0] if order_book.asks else None

                if best_ask_order and order.price >= best_ask_order.price:
                    await self._execute_aggressive_limit_order(uow, order_book, order)
            else:  # SELL LIMIT order
                best_bid_order = order_book.bids[0] if order_book.bids else None

                if best_bid_order and order.price <= best_bid_order.price:
                    await self._execute_aggressive_limit_order(uow, order_book, order)

        if create_schema.order_type == models.order.OrderType.MARKET:
            await self._execute_market_order(
                uow=uow,
                order_book_manager=order_book_manager,
                instrument_id=create_schema.instrument_id,
                order=order,
            )

        order_book_manager.clear_order_book(create_schema.instrument_id)

        return order

    async def _get_locked_amounts(
        self,
        uow: UnitOfWork,
        create_schema: schemas.orders.Create,
        rub_balance: schemas.balance.Read,
        instrument_balance: schemas.balance.Read,
    ) -> dict[str, int | None]:
        if create_schema.order_type == models.order.OrderType.LIMIT:
            filled = 0
            if create_schema.direction == models.order.Direction.BUY:
                async with uow.postgres_session.begin_nested():
                    with threading.Lock():
                        locked_money = await self.repo.sum_locked_money(uow, create_schema.user_id)

                if create_schema.price is None:
                    raise ValueError("Limit orders require price")

                required_money = create_schema.qty * create_schema.price
                available_money = rub_balance.amount - locked_money

                if available_money < required_money:
                    raise services.exceptions.InsufficientBalanceError(
                        create_schema.user_id,
                        "RUB",
                    )

                locked_money_amount, locked_instrument_amount = required_money, None

            else:  # LIMIT SELL
                async with uow.postgres_session.begin_nested():
                    with threading.Lock():
                        locked_instrument = await self.repo.sum_locked_instrument(
                            uow,
                            create_schema.user_id,
                            instrument_balance.instrument_id,
                        )

                available_instrument = instrument_balance.amount - locked_instrument

                if available_instrument < create_schema.qty:
                    instrument = await self.instrument_service.read_by_id(
                        uow,
                        instrument_balance.instrument_id,
                    )
                    raise services.exceptions.InsufficientBalanceError(
                        create_schema.user_id,
                        instrument.ticker,
                    )

                locked_money_amount, locked_instrument_amount = None, create_schema.qty

        else:  # MARKET ORDER
            filled, locked_money_amount, locked_instrument_amount = None, None, None

        return dict(
            filled=filled,
            locked_money_amount=locked_money_amount,
            locked_instrument_amount=locked_instrument_amount,
        )

    async def _execute_market_order(
        self,
        uow: UnitOfWork,
        order_book_manager: utils.OrderBookManager,
        instrument_id: UUID,
        order: schemas.orders.Read,
    ) -> None:
        order_book = await order_book_manager.get_order_book(
            uow,
            instrument_id,
            core.schemas.PaginationParams(limit=100),
            refresh=True,
        )

        remaining_qty = order.qty
        while remaining_qty > 0:
            if order.direction == models.order.Direction.BUY:
                best_ask_order = order_book.asks[0] if order_book.asks else None

                if (
                    not best_ask_order
                    or (available_qty := (best_ask_order.qty - best_ask_order.filled)) <= 0
                ):
                    break

                trade_qty = min(remaining_qty, available_qty)

                await order_book.execute_trade(
                    uow,
                    buy_order=order,
                    sell_order=best_ask_order,
                    quantity=trade_qty,
                )

                remaining_qty -= trade_qty

            else:  # SELL
                best_bid_order = order_book.bids[0] if order_book.bids else None

                if (
                    not best_bid_order
                    or (available_qty := (best_bid_order.qty - best_bid_order.filled)) <= 0
                ):
                    break

                trade_qty = min(remaining_qty, available_qty)

                await order_book.execute_trade(
                    uow,
                    buy_order=best_bid_order,
                    sell_order=order,
                    quantity=trade_qty,
                )

                remaining_qty -= trade_qty

        if remaining_qty != 0:
            order_book_manager.clear_order_book(instrument_id)
            raise services.exceptions.OrderRejectedError(order.id, order.qty, remaining_qty)

    async def _execute_aggressive_limit_order(
        self,
        uow: UnitOfWork,
        order_book: utils.orderbook.OrderBook,
        order: schemas.orders.Read,
    ) -> None:
        remaining_qty = order.qty - (order.filled or 0)

        assert order.price is not None

        current_order = order
        while remaining_qty > 0:
            if order.direction == models.order.Direction.BUY:
                best_ask_order = order_book.asks[0] if order_book.asks else None

                if (
                    not best_ask_order
                    or best_ask_order.price is None
                    or best_ask_order.price > order.price
                    or (available_qty := (best_ask_order.qty - (best_ask_order.filled or 0))) <= 0
                ):
                    break

                trade_qty = min(remaining_qty, available_qty)

                updated_orders = await order_book.execute_trade(
                    uow,
                    current_order,  # type: ignore[valid-type]
                    best_ask_order,
                    trade_qty,
                )
                current_order = updated_orders[0]

                remaining_qty -= trade_qty

            else:  # LIMIT SELL
                best_bid_order = order_book.bids[0] if order_book.bids else None

                if (
                    not best_bid_order
                    or best_bid_order.price is None
                    or best_bid_order.price < order.price
                    or (available_qty := (best_bid_order.qty - (best_bid_order.filled or 0))) == 0
                ):
                    break

                trade_qty = min(remaining_qty, available_qty)

                updated_orders = await order_book.execute_trade(
                    uow,
                    best_bid_order,
                    current_order,  # type: ignore[valid-type]
                    trade_qty,
                )
                current_order = updated_orders[1]

                remaining_qty -= trade_qty

    async def refund_locked_amount(
        self,
        uow: UnitOfWork,
        order: schemas.orders.Read,
    ) -> None:
        self.balance_service = services.Balances()
        self.instrument_service = services.Instruments()
        if order.locked_money_amount and order.locked_money_amount > 0:
            rub_instrument = await self.instrument_service.read_by_ticker(uow, "RUB")

            balance = await self.balance_service.get_or_create_user_balance(
                uow,
                order.user_id,
                rub_instrument.id,
            )
            new_amount = balance.amount + order.locked_money_amount

            await self.balance_service.update_by_id(
                uow,
                {"user_id": order.user_id, "instrument_id": rub_instrument.id},
                schemas.balance.Update(amount=new_amount),
            )

            await self.update_by_id(
                uow,
                order.id,
                schemas.orders.Update(locked_money_amount=0),
            )

        if order.locked_instrument_amount and order.locked_instrument_amount > 0:
            balance = await self.balance_service.get_or_create_user_balance(
                uow,
                order.user_id,
                order.instrument.id,
            )
            new_amount = balance.amount + order.locked_instrument_amount

            await self.balance_service.update_by_id(
                uow,
                {"user_id": order.user_id, "instrument_id": order.instrument.id},
                schemas.balance.Update(amount=new_amount),
            )

            await self.update_by_id(
                uow,
                order.id,
                schemas.orders.Update(locked_instrument_amount=0),
            )
