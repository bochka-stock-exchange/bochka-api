from fastapi import APIRouter, HTTPException, status

import src.api.v1.dependencies as dependencies
import src.schemas.instrument as instrument_schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register", response_model=user_schemas.UserRead)
async def register(
    user_create: user_schemas.UserCreate,
    users_service: dependencies.UsersService,
    session: dependencies.Session,
):
    try:
        user = await users_service.create(session, user_create)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/profile", response_model=user_schemas.UserRead)
async def get_profile(
    current_user: dependencies.CurrentUser,
):
    return current_user


@router.get("/profile-admin", response_model=user_schemas.UserRead)
async def get_profile_admin(
    current_user: dependencies.AdminUser,
):
    return current_user


@router.get("/instrument", response_model=list[instrument_schemas.InstrumentRead])
async def get_instruments(
    instruments_service: dependencies.InstrumentsService, session: dependencies.Session
):
    try:
        instruments = await instruments_service.read_all(session)
        return instruments
    except service_exceptions.EntityReadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError()


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError()
