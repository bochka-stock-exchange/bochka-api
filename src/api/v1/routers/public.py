from fastapi import APIRouter, HTTPException, status

import src.api.v1.dependencies as dependencies
import src.schemas as schemas
import src.services as services

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
        user = await users_service.create(session, user_create)
        return user
    except services.exceptions.EntityCreateError as e:
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
    instruments_service: dependencies.InstrumentsService, session: dependencies.DBSession
):
    try:
        instruments = await instruments_service.read_all(session)
        return instruments
    except services.exceptions.EntityReadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError()


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError()
