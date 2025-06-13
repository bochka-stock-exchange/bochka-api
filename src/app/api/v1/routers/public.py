from fastapi import APIRouter

from src import core
from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/register", response_model=schemas.users.Auth)
async def register(
    user_create: schemas.users.Create,
    auth_service: dependencies.services.Auth,
    uow: dependencies.uow.Postgres,
):
    return await auth_service.auth_user(uow, user_create)


@router.get("/instrument", response_model=list[schemas.instruments.Read])
async def get_instruments(
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await instruments_service.read_many(
        uow, pagination=core.schemas.PaginationParams(limit=1000)
    )


@router.get("/instrument/tickers")
async def get_instruments_tickers(
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await instruments_service.get_all_instruments(uow)


@router.get("/orderbook/{ticker}", response_model=schemas.orders.OrderBook)
async def get_orderbook(
    uow: dependencies.uow.Postgres,
    instruments_service: dependencies.services.Orders,
    ticker: str,
    limit: int = 10,
):
    return await instruments_service.get_order_book(uow, ticker, limit)


@router.get("/transactions/{ticker}", response_model=list[schemas.transactions.Read])
async def get_transactions(
    uow: dependencies.uow.Postgres,
    instruments_service: dependencies.services.Instruments,
    transactions_service: dependencies.services.Transactions,
    ticker: str,
    limit: int = 10,
):
    instrument = await instruments_service.read_by_ticker(uow, ticker)
    return await transactions_service.read_many(
        uow,
        schemas.transactions.Filters(instrument_id=instrument.id),
        schemas.transactions.SortParams(
            sort_by=schemas.transactions.SortFields.CREATED_AT, ascending=False
        ),
        core.schemas.PaginationParams(limit=limit),
    )
