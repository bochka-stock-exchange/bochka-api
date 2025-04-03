from fastapi import APIRouter

from src.app import schemas
from src.app.api.v1 import dependencies

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register", response_model=schemas.UserRead)
async def register(
    user_create: schemas.UserCreate,
    users_service: dependencies.UsersService,
    session: dependencies.DBSession,
):
    return await users_service.create(session, user_create)


@router.get("/profile", response_model=schemas.UserRead)
async def get_profile(
    current_user: dependencies.CurrentUser,
):
    return current_user


@router.get("/profile-admin", response_model=schemas.UserRead)
async def get_profile_admin(
    current_user: dependencies.AdminUser,
):
    return current_user


@router.get("/instrument", response_model=list[schemas.InstrumentRead])
async def get_instruments(
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.DBSession,
):
    return await instruments_service.read_all(session)


@router.get("/users-all")
async def get_all_users(
    users_service: dependencies.UsersService,
    session: dependencies.DBSession,
    page: int = 1,
    limit: int = 10,
) -> list[schemas.UserRead]:
    return await users_service.read_all(session, page=page, limit=limit)


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError
