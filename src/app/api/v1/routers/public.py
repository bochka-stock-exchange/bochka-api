from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies
from src.core.schemas import PaginationParams

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
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await service.read_many(uow, pagination=PaginationParams(limit=1000))


@router.get("/instrument/tickers")
async def get_instruments_tickers(
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await service.get_all_instruments(uow)


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError
