from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserRead
from src.services.base import BaseService


class UserService(BaseService[UserCreate, UserRead, UserCreate]):
    def __init__(self):
        self.repo = UserRepository()
        super().__init__(
            self.repo,
            create_schema=UserCreate,
            read_schema=UserRead,
            update_schema=UserCreate,
        )

    def pre_create(self, data: dict) -> dict:
        data["api_key"] = "key-" + str(uuid7())
        return data

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> Optional[UserRead]:
        try:
            user_data = await self.repo.get_by_api_key(session, api_key)
        except Exception as e:
            raise e
        return self.read_schema.model_validate(user_data)
