from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/register", response_model=schemas.users.Read)
async def register(
    user_create: schemas.users.Create,
    service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
):
    return await service.create(uow, user_create)


@router.get("/instrument", response_model=list[schemas.instruments.Read])
async def get_instruments(
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await service.read_many(uow)


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError
