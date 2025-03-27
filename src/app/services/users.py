from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src import core
from src.app import repositories, schemas


class Users(core.services.BaseCRUD[schemas.UserCreate, schemas.UserRead, schemas.UserCreate]):
    def __init__(self):
        self.repo = repositories.Users()
        super().__init__(
            self.repo,
            create_schema=schemas.UserCreate,
            read_schema=schemas.UserRead,
            update_schema=schemas.UserCreate,
        )

    @staticmethod
    def prepare_data(data: dict) -> dict:
        data["api_key"] = "key-" + str(uuid7())
        return data

    async def get_by_api_key(
        self,
        session: AsyncSession,
        api_key: str,
    ) -> schemas.UserRead | None:
        try:
            user_data = await self.repo.get_by_api_key(session, api_key)
        except core.repositories.exceptions.EntityReadError as e:
            raise core.services.exceptions.EntityReadError(self.__class__.__name__, str(e)) from e

        return self.read_schema.model_validate(user_data)
