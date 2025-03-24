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
    return 1


@router.post("/register", response_model=user_schemas.UserRead)
async def register(
    user_create: user_schemas.UserCreate,
    service: UserServiceDependency,
    session: SessionDependency,
):
    try:
        user = await service.create(session, user_create)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/profile", response_model=user_schemas.UserRead)
async def get_profile(
    current_user: Annotated[user_schemas.UserRead, Depends(get_current_user)],
):
    return current_user


@router.get("/check-admin", response_model=user_schemas.UserRead)
async def check_admin(
    current_user: Annotated[user_schemas.UserRead, Depends(get_admin_user)],
):
    return current_user


@router.get("/instrument", response_model=list[instrument_schemas.InstrumentRead])
async def get_instruments(service: InstrumentServiceDependency, session: SessionDependency):
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
    raise NotImplementedError()


"""
async def create_t(
    session: AsyncSession,
    data,
):
    instance = User(**data)
    session.add(instance)
    await session.flush()
    await session.refresh(instance)
    return instance


async def get_t(session: AsyncSession, id: str):
    return await session.get(User, id)


async def update_t(
    session: AsyncSession,
    id: str,
    data,
):
    instance = await get_t(session, id)

    if instance:
        for key, value in data.items():
            if value:
                setattr(instance, key, value)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)

    return instance


@router.patch("/users/update")
async def update_user_test(
    user_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    name: Optional[str] = None,
    role: Optional[str] = None,
    api_key: Optional[str] = None,
):
    if role and role not in UserRole:
        return False
    async with uow:
        a = await update_t(
            uow.session,
            user_id,
            {"name": name, "role": role, "api_key": api_key},
        )
    return a


@router.post("/users/create")
async def create_user_test(uow: Annotated[UnitOfWork, Depends(get_uow)]):
    async with uow:
        a = await create_t(
            uow.session,
            {"name": "Pudge", "role": UserRole.USER, "api_key": "asdfasdfas"},
        )
        return a


@router.get("/users/get")
async def get_user_test(
    user_id: str, uow: Annotated[UnitOfWork, Depends(get_uow)]
):
    async with uow:
        a = await get_t(uow.session, user_id)
        return a


@router.get("/users/get/all")
async def get_all_users(uow: Annotated[UnitOfWork, Depends(get_uow)]):
    async with uow:
        result = await uow.session.execute(select(User))
        return result.scalars().all()
"""
