from sqlalchemy import select

from src import core
from src.app import models


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def read_by_name(
        self, uow: core.UnitOfWork, name: str, *, include_deleted: bool = False
    ) -> models.User | None:
        try:
            session = uow.postgres_session
            query = select(self.model).where(self.model.name == name)

            if not include_deleted and issubclass(self.model, core.models.sqlalchemy.SoftDelete):
                query = query.where(self.model.deleted_at.is_(None))

            user = await session.scalar(query)

            if not user:
                self.logger.info(
                    "User not found by name",
                    extra={"user_name": name, "exists": False},
                )
            return user
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
