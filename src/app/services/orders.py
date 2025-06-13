import json
from typing import cast
from uuid import UUID

from src import core
from src.app import models, repositories, schemas, services

from . import exceptions

import aio_pika

async def setup_rabbitmq():
    connection = await aio_pika.connect_robust("amqp://guest:guest@127.0.0.1/")
    channel = await connection.channel()

    # Declare exchange
    exchange = await channel.declare_exchange(
        "order_processing_exchange",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    # Declare queue
    queue = await channel.declare_queue("order_processing", durable=True)

    # Bind queue
    await queue.bind(exchange, routing_key="order_processing")

    return exchange

class Orders(
    core.services.BaseCRUD[
        schemas.orders.Create,
        schemas.orders.Read,
        schemas.orders.Update,
        schemas.orders.Filters,
        schemas.orders.SortParams,
        models.Order,
    ]
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

        self.order_handlers = {
            ("MARKET", "BUY"): self._handle_market_buy,
            ("MARKET", "SELL"): self._handle_market_sell,
            ("LIMIT", "BUY"): self._handle_limit_buy,
            ("LIMIT", "SELL"): self._handle_limit_sell,
        }

        self.instruments_service = services.Instruments()
        self.balances_service = services.Balances()
        self.transactions_service = services.Transactions()

    async def _return_locked_amount(self, uow: core.UnitOfWork, order_id: UUID) -> None:
        order = await self.read_by_id(uow, order_id)
        rub_instrument = await self.instruments_service.read_by_ticker(uow, "RUB")

        if order.locked_amount > 0:
            await self.update_by_id(uow, order_id, schemas.orders.Update(locked_amount=0))

            instrument_id = (
                rub_instrument.id
                if order.direction == models.OrderDirection.BUY
                else order.instrument.id
            )

            balance = await self.balances_service.get_or_create_user_balance(
                uow, order.user.id, instrument_id
            )
            new_balance_locked_amount = balance.locked_amount - order.locked_amount
            await self.balances_service.update_by_id(
                uow,
                {"user_id": order.user.id, "instrument_id": instrument_id},
                schemas.balance.Update(locked_amount=new_balance_locked_amount),
            )

    async def _create_transaction(
        self,
        uow: core.UnitOfWork,
        buy_order_id: UUID,
        sell_order_id: UUID,
        instrument_id: UUID,
        qty: int,
        price: int,
    ) -> None:
        await self.transactions_service.create(
            uow,
            schemas.transactions.Create(
                buy_order_id=buy_order_id,
                sell_order_id=sell_order_id,
                instrument_id=instrument_id,
                qty=qty,
                price=price,
            ),
        )

    async def _update_balances(
        self,
        uow: core.UnitOfWork,
        buy_order_id: UUID,
        sell_order_id: UUID,
        qty: int,
        price: int,
    ) -> None:
        sell_order = await self.read_by_id(uow, sell_order_id)
        buy_order = await self.read_by_id(uow, buy_order_id)

        new_sell_locked_amount = sell_order.locked_amount - qty
        await self.update_by_id(
            uow, sell_order.id, schemas.orders.Update(locked_amount=new_sell_locked_amount)
        )

        await self.balances_service.transfer(
            uow,
            from_user_id=sell_order.user.id,
            to_user_id=buy_order.user.id,
            instrument_id=sell_order.instrument.id,
            amount=qty,
        )

        rub_instrument = await self.instruments_service.read_by_ticker(uow, "RUB")

        new_buy_locked_amount = buy_order.locked_amount - price
        await self.update_by_id(
            uow, buy_order.id, schemas.orders.Update(locked_amount=new_buy_locked_amount)
        )

        await self.balances_service.transfer(
            uow,
            from_user_id=buy_order.user.id,
            to_user_id=sell_order.user.id,
            instrument_id=rub_instrument.id,
            amount=price,
        )

    async def _execute_trade(
        self,
        uow: core.UnitOfWork,
        buy_order: schemas.orders.Read,
        sell_order: schemas.orders.Read,
        executed_qty: int,
        price: int,
    ) -> None:
        executed_price = price * executed_qty

        await self._update_balances(
            uow,
            buy_order_id=buy_order.id,
            sell_order_id=sell_order.id,
            qty=executed_qty,
            price=executed_price,
        )

        await self._create_transaction(
            uow,
            buy_order_id=buy_order.id,
            sell_order_id=sell_order.id,
            instrument_id=buy_order.instrument.id,
            qty=executed_qty,
            price=executed_price,
        )

        new_filled_buy = buy_order.filled + executed_qty
        buy_status = (
            models.OrderStatus.EXECUTED
            if new_filled_buy == buy_order.qty
            else models.OrderStatus.PARTIALLY_EXECUTED
        )

        await self.update_by_id(
            uow,
            buy_order.id,
            schemas.orders.Update(
                filled=new_filled_buy,
                status=buy_status,
            ),
        )

        if buy_status == models.OrderStatus.EXECUTED:
            await self._return_locked_amount(uow, buy_order.id)

        new_filled_sell = sell_order.filled + executed_qty
        sell_status = (
            models.OrderStatus.EXECUTED
            if new_filled_sell == sell_order.qty
            else models.OrderStatus.PARTIALLY_EXECUTED
        )

        if sell_status == models.OrderStatus.EXECUTED:
            await self._return_locked_amount(uow, sell_order.id)

        await self.update_by_id(
            uow, sell_order.id, schemas.orders.Update(filled=new_filled_sell, status=sell_status)
        )

    async def _find_best_order(
        self,
        uow: core.UnitOfWork,
        instrument_id: UUID,
        order_direction: models.OrderDirection,
        price: int | None = None,
    ) -> schemas.orders.Read | None:
        price_from = price if order_direction == models.OrderDirection.BUY else None
        price_to = price if order_direction == models.OrderDirection.SELL else None

        orders = await self.read_many(
            uow,
            schemas.orders.Filters(
                direction=order_direction,
                order_type=models.OrderType.LIMIT,
                instrument_id=instrument_id,
                status=[models.OrderStatus.NEW, models.OrderStatus.PARTIALLY_EXECUTED],
                price_from=price_from,
                price_to=price_to,
            ),
            schemas.orders.SortParams(
                sort_by=schemas.orders.SortFields.PRICE,
                ascending=order_direction == models.OrderDirection.SELL,
            ),
            core.schemas.PaginationParams(limit=1),
        )

        if not orders:
            return None

        return orders[0]

    async def reserve(
        self, uow: core.UnitOfWork, user_id: UUID, instrument_id: UUID, order_id: UUID, amount: int
    ) -> None:
        balance = await self.balances_service.get_or_create_user_balance(
            uow, user_id, instrument_id
        )

        new_locked_amount = balance.locked_amount + amount

        new_available_amount = balance.available_amount - amount

        if new_available_amount < 0:
            instrument = await self.instruments_service.read_by_id(uow, instrument_id)
            raise services.exceptions.InsufficientBalanceError(user_id, instrument.ticker)

        await self.balances_service.update_by_id(
            uow,
            {"user_id": user_id, "instrument_id": instrument_id},
            schemas.balance.Update(locked_amount=new_locked_amount),
        )

        await self.update_by_id(uow, order_id, schemas.orders.Update(locked_amount=amount))

    async def _handle_market_buy(self, uow: core.UnitOfWork, order: schemas.orders.Read) -> None:
        rub_instrument = await self.instruments_service.read_by_ticker(uow, "RUB")

        remaining = order.qty - order.filled

        while remaining > 0:
            sell_order = await self._find_best_order(
                uow, order.instrument.id, models.OrderDirection.SELL
            )

            if not sell_order:
                raise exceptions.OrderRejectedError(order.id, order.qty, order.qty - remaining)

            sell_available = sell_order.qty - sell_order.filled
            executed_qty = min(sell_available, remaining)
            required_rub = executed_qty * cast(int, sell_order.price)

            await self.reserve(
                uow,
                order.user_id,
                rub_instrument.id,
                order.id,
                required_rub,
            )

            await self._execute_trade(
                uow, order, sell_order, executed_qty, cast(int, sell_order.price)
            )

            remaining -= executed_qty

    async def _handle_market_sell(self, uow: core.UnitOfWork, order: schemas.orders.Read) -> None:
        remaining = order.qty - order.filled

        while remaining > 0:
            buy_order = await self._find_best_order(
                uow, order.instrument.id, models.OrderDirection.BUY
            )
            if not buy_order:
                raise exceptions.OrderRejectedError(order.id, order.qty, order.qty - remaining)

            executed_qty = min(buy_order.qty - buy_order.filled, order.qty - order.filled)

            await self.reserve(uow, order.user_id, order.instrument.id, order.id, executed_qty)

            await self._execute_trade(
                uow, buy_order, order, executed_qty, cast(int, buy_order.price)
            )

            remaining -= executed_qty

    async def _handle_limit_buy(self, uow: core.UnitOfWork, order: schemas.orders.Read) -> None:
        rub_instrument = await self.instruments_service.read_by_ticker(uow, "RUB")

        await self.reserve(
            uow, order.user_id, rub_instrument.id, order.id, cast(int, order.price) * order.qty
        )

        remaining = order.qty - order.filled
        while remaining > 0:
            sell_order = await self._find_best_order(
                uow, order.instrument.id, models.OrderDirection.SELL, order.price
            )
            if not sell_order:
                break

            executed_qty = min(sell_order.qty - sell_order.filled, order.qty - order.filled)

            await self._execute_trade(
                uow, order, sell_order, executed_qty, cast(int, sell_order.price)
            )

            remaining -= executed_qty

    async def _handle_limit_sell(self, uow: core.UnitOfWork, order: schemas.orders.Read) -> None:
        await self.reserve(uow, order.user_id, order.instrument.id, order.id, order.qty)

        remaining = order.qty - order.filled
        while remaining > 0:
            buy_order = await self._find_best_order(
                uow, order.instrument.id, models.OrderDirection.BUY, order.price
            )
            if not buy_order:
                break

            executed_qty = min(buy_order.qty - buy_order.filled, order.qty - order.filled)

            await self._execute_trade(
                uow, buy_order, order, executed_qty, cast(int, buy_order.price)
            )

            remaining -= executed_qty

    async def _check_market_order_can_be_done(
        self, uow: core.UnitOfWork, order: schemas.orders.Read
    ) -> None:
        match order.direction:
            case models.OrderDirection.BUY:
                remaining = order.qty - order.filled

                rub_instrument = await self.instruments_service.read_by_ticker(uow, "RUB")
                user_rub_balance = await self.balances_service.get_or_create_user_balance(
                    uow, order.user.id, rub_instrument.id
                )
                available_balance = user_rub_balance.available_amount

                while remaining > 0:
                    sell_order = await self._find_best_order(
                        uow, order.instrument.id, models.OrderDirection.SELL
                    )

                    if not sell_order:
                        raise exceptions.OrderRejectedError(
                            order.id, order.qty, order.qty - remaining
                        )

                    sell_available = sell_order.qty - sell_order.filled
                    executed_qty = min(sell_available, remaining)
                    required_rub = executed_qty * cast(int, sell_order.price)

                    available_balance -= required_rub
                    if available_balance < 0:
                        raise services.exceptions.InsufficientBalanceError(
                            order.user.id, rub_instrument.ticker
                        )

                    remaining -= executed_qty

            case models.OrderDirection.SELL:
                remaining = order.qty - order.filled

                user_balance = await self.balances_service.get_or_create_user_balance(
                    uow, order.user.id, order.instrument.id
                )
                available_balance = user_balance.available_amount

                while remaining > 0:
                    buy_order = await self._find_best_order(
                        uow, order.instrument.id, models.OrderDirection.BUY
                    )
                    if not buy_order:
                        raise exceptions.OrderRejectedError(
                            order.id, order.qty, order.qty - remaining
                        )

                    executed_qty = min(buy_order.qty - buy_order.filled, order.qty - order.filled)

                    available_balance -= executed_qty
                    if available_balance < 0:
                        raise services.exceptions.InsufficientBalanceError(
                            order.user.id, order.instrument.ticker
                        )

                    remaining -= executed_qty

    async def create(
        self,
        uow: core.UnitOfWork,
        order_data: schemas.orders.Create,
        additional_data: dict,
    ) -> schemas.orders.Read:
        instrument = await self.instruments_service.read_by_ticker(uow, order_data.ticker)
        additional_data["instrument_id"] = instrument.id

        order = await super().create(uow, order_data, additional_data=additional_data)

        if order.order_type == models.OrderType.MARKET:
            await self._check_market_order_can_be_done(uow, order)

        self.rabbitmq_publisher = await setup_rabbitmq()

        order_msg = order.model_dump()["id"] = str(order.id)

        try:
            message = aio_pika.Message(
                body=json.dumps(order_msg).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self.rabbitmq_publisher.publish(
                message,
                routing_key="order_processing"
            )
            self.logger.info("Published order {order.id} to RabbitMQ")
        except Exception:
            self.logger.exception("Failed to publish order")
            # Consider adding retry logic here

        return order

    async def get_order_book_levels(
        self,
        uow: core.UnitOfWork,
        instrument_id: UUID,
        direction: models.OrderDirection,
        limit: int,
    ) -> list[schemas.orders.OrderBookLevel]:
        raw_levels = await self.repo.get_order_book_levels(uow, instrument_id, direction, limit)

        return [schemas.orders.OrderBookLevel(**level) for level in raw_levels]

    async def get_order_book(
        self, uow: core.UnitOfWork, ticker: str, limit: int
    ) -> schemas.orders.OrderBook:
        instrument = await self.instruments_service.read_by_ticker(uow, ticker)

        bid_levels = await self.get_order_book_levels(
            uow, instrument.id, models.OrderDirection.BUY, limit
        )

        ask_levels = await self.get_order_book_levels(
            uow, instrument.id, models.OrderDirection.SELL, limit
        )

        return schemas.orders.OrderBook(bid_levels=bid_levels, ask_levels=ask_levels)

    async def cancel_order(self, uow: core.UnitOfWork, order_id: UUID):
        order = await self.read_by_id(uow, order_id)

        await self._return_locked_amount(uow, order.id)

        await self.update_by_id(
            uow, order_id, schemas.orders.Update(status=models.order.OrderStatus.CANCELLED)
        )

        await self.repo.delete_by_id(uow, order_id)
