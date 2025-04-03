from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import models


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def get_by_api_key(self, session: AsyncSession, api_key: str) -> models.User | None:
        try:
            return await session.scalar(select(models.User).where(models.User.api_key == api_key))
        except Exception as e:
            raise core.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
