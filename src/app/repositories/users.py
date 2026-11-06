from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src import core
from src.app import models

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Users(core.repositories.sqlalchemy.BaseCRUD[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def read_by_name(
        self,
        uow: UnitOfWork,
        name: str,
        *,
        include_deleted: bool = False,
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
        except Exception:
            raise
