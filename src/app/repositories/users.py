from sqlalchemy import select

from src import core
from src.app import models


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def get_by_api_key(self, uow: core.UnitOfWork, api_key: str) -> models.User | None:
        session = uow.postgres_session
        try:
            return await session.scalar(select(models.User).where(models.User.api_key == api_key))
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
