from typing import Optional

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import manager
from src.models import User
from src.models.user import UserRole

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/healthcheck")
async def healthcheck():
    return 1


@router.post("/register")
async def register():
    raise NotImplementedError()


@router.get("/instrument")
async def get_instruments():
    raise NotImplementedError()


@router.get("/orderbook/{ticker}")
async def get_orderbook(ticker: str):
    raise NotImplementedError()


@router.get("/transactions/{ticker}")
async def get_transactions(ticker: str):
    raise NotImplementedError()


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
    name: Optional[str] = None,
    role: Optional[str] = None,
    api_key: Optional[str] = None,
):
    if role and role not in UserRole:
        return False
    async with manager.begin_transaction_session() as sess:
        a = await update_t(
            sess,
            user_id,
            {"name": name, "role": role, "api_key": api_key},
        )
    return a


@router.post("/users/create")
async def create_user_test():
    async with manager.begin_transaction_session() as sess:
        a = await create_t(
            sess,
            {"name": "Pudge", "role": UserRole.USER, "api_key": "asdfasdfas"},
        )
        return a


@router.get("/users/get")
async def get_user_test(user_id: str):
    async with manager.begin_transaction_session() as sess:
        a = await get_t(sess, user_id)
        return a


@router.get("/users/get/all")
async def get_all_users():
    async with manager.begin_transaction_session() as sess:
        result = await sess.execute(select(User))
        return result.scalars().all()
