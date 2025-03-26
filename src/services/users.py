from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

import src.repositories as repositories
import src.schemas as schemas
import src.services as services


class Users(services.BaseCRUD[schemas.UserCreate, schemas.UserRead, schemas.UserCreate]):
    def __init__(self):
        self.repo = repositories.Users()
        super().__init__(
            self.repo,
            create_schema=schemas.UserCreate,
            read_schema=schemas.UserRead,
            update_schema=schemas.UserCreate,
        )

    def prepare_data(self, data: dict) -> dict:
        data["api_key"] = "key-" + str(uuid7())
        return data

    async def get_by_api_key(
        self, session: AsyncSession, api_key: str
    ) -> Optional[schemas.UserRead]:
        try:
            user_data = await self.repo.get_by_api_key(session, api_key)
        except repositories.exceptions.EntityReadError as e:
            raise services.exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        return self.read_schema.model_validate(user_data)
