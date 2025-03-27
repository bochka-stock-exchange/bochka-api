from fastapi import APIRouter, HTTPException, status

from src import core
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
    try:
        return await users_service.create(session, user_create)
    except core.services.exceptions.EntityCreateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


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
    try:
        return await instruments_service.read_all(session)
    except core.services.exceptions.EntityReadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError
