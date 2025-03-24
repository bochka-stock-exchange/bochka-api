from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import src.schemas.instrument as instrument_schemas
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.api.v1.dependencies import (
    InstrumentServiceDependency,
    SessionDependency,
    UserServiceDependency,
    get_admin_user,
    get_current_user,
)

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/healthcheck")
async def healthcheck():
    """
    Healthcheck endpoint.
    
    Returns:
        int: The constant value 1, indicating that the server is operational.
    """
    return 1


@router.post("/register", response_model=user_schemas.UserRead)
async def register(
    user_create: user_schemas.UserCreate,
    service: UserServiceDependency,
    session: SessionDependency,
):
    """Registers a new user.
    
    Attempts to create a new user using the provided creation data and returns the
    created user. Raises an HTTPException with status code 400 if an error occurs during
    user creation.
    """
    try:
        user = await service.create(session, user_create)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/profile", response_model=user_schemas.UserRead)
async def get_profile(
    current_user: Annotated[user_schemas.UserRead, Depends(get_current_user)],
):
    """
    Retrieves the current user's profile.
    
    The authenticated user's information is obtained via dependency injection and returned directly.
    """
    return current_user


@router.get("/profile-admin", response_model=user_schemas.UserRead)
async def get_profile_admin(
    current_user: Annotated[user_schemas.UserRead, Depends(get_admin_user)],
):
    """
    Retrieves the current admin user's profile.
    
    This endpoint returns the profile details of an authenticated admin user.
    """
    return current_user


@router.get("/instrument", response_model=list[instrument_schemas.InstrumentRead])
async def get_instruments(service: InstrumentServiceDependency, session: SessionDependency):
    """
    Retrieves all instruments.
    
    Asynchronously fetches instrument records using the provided service and session.
    Raises an HTTPException with a 400 status code if an error occurs during retrieval.
    
    Returns:
        list: A list of instrument records.
    """
    try:
        instruments = await service.read_all(session)
        return instruments
    except service_exceptions.EntityReadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError()


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    """
    Retrieves transactions for the specified ticker.
    
    This endpoint is not implemented yet.
    
    Args:
        ticker (str): The ticker symbol for which transactions would be retrieved.
    
    Raises:
        NotImplementedError: Always raised as the functionality is pending implementation.
    """
    raise NotImplementedError()
