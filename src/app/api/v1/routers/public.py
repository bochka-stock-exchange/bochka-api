from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Query

from src.app import schemas, utils
from src.app.api import dependencies
from src.core.schemas import PaginationParams
from src.core.utils.decorators import retry_on_serialization

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/register", response_model=schemas.users.Auth)
@retry_on_serialization()
async def register(
    user_create: schemas.users.Create,
    auth_service: dependencies.services.Auth,
    uow: dependencies.uow.Postgres,
):
    return await auth_service.auth_user(uow, user_create)


@router.get("/instrument", response_model=list[schemas.instruments.Read])
async def get_instruments(
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await service.read_many(uow, pagination=PaginationParams(limit=0))


@router.get("/instrument/tickers", response_model=list[schemas.instruments.ReadTicker])
async def get_instruments_tickers(
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await service.get_all_instruments(uow)


@router.get("/orderbook/{ticker}", response_model=schemas.orders.OrderBookRead)
@retry_on_serialization()
async def get_orderbook(
    uow: dependencies.uow.Postgres,
    instruments_service: dependencies.services.Instruments,
    ticker: schemas.instruments.Ticker,
    pagination: Annotated[schemas.orders.OrderBookPaginationParams, Query()],
):
    instrument = await instruments_service.read_by_ticker(uow, ticker)

    order_book = await utils.get_order_book_manager().get_order_book(
        uow,
        instrument.id,
        pagination,
        refresh=True,
    )

    def extract_levels(heap: utils.orderbook.OrderHeap, *, is_bid: bool) -> list[dict[str, int]]:
        price_map = defaultdict(int)

        for order in heap:
            if order.price is None or order.price < 0:
                continue
            qty_remaining = order.qty - (order.filled or 0)
            if qty_remaining > 0:
                price_map[order.price] += qty_remaining

        sorted_prices = sorted(price_map.items(), key=lambda x: x[0], reverse=is_bid)

        return [{"price": price, "qty": qty} for price, qty in sorted_prices]

    bids = extract_levels(order_book.bids, is_bid=True)
    asks = extract_levels(order_book.asks, is_bid=False)

    return schemas.orders.OrderBookRead(
        bid_levels=[schemas.orders.OrderBookLevel.model_validate(bid) for bid in bids],
        ask_levels=[schemas.orders.OrderBookLevel.model_validate(ask) for ask in asks],
    )


@router.get("/transactions/{ticker}", response_model=list[schemas.transactions.Read])
@retry_on_serialization()
async def get_transactions(
    uow: dependencies.uow.Postgres,
    transactions_service: dependencies.services.Transactions,
    instruments_service: dependencies.services.Instruments,
    ticker: schemas.instruments.Ticker,
    pagination: Annotated[schemas.transactions.TransactionsPaginationParams, Query()],
):
    instrument = await instruments_service.read_by_ticker(uow, ticker)

    return await transactions_service.read_many(
        uow,
        filters=schemas.transactions.Filters(instrument_id=instrument.id),
        sorting=schemas.transactions.SortParams(
            sort_by=schemas.transactions.SortFields.CREATED_AT,
        ),
        pagination=pagination,
    )
