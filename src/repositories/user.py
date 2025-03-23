from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.repositories.base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> Optional[User]:
        user = await session.scalar(select(User).where(User.api_key == api_key))
        return user
