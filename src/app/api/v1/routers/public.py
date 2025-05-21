from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register", response_model=schemas.users.Read)
async def register(
    user_create: schemas.users.Create,
    users_service: dependencies.UsersService,
    uow: dependencies.UoWPostgres,
):
    return await users_service.create(uow, user_create)


@router.get("/profile", response_model=schemas.users.Read)
async def get_profile(
    current_user: dependencies.CurrentUser,
):
    return current_user


@router.get("/profile-admin", response_model=schemas.users.Read)
async def get_profile_admin(
    current_user: dependencies.AdminUser,
):
    return current_user


@router.get("/instrument", response_model=list[schemas.instruments.Read])
async def get_instruments(
    instruments_service: dependencies.InstrumentsService,
    uow: dependencies.UoWPostgres,
):
    return await instruments_service.read_many(uow)


@router.get("/users-all")
async def get_all_users(
    users_service: dependencies.UsersService,
    uow: dependencies.UoWPostgres,
) -> list[schemas.users.Read]:
    return await users_service.read_many(uow)


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError
