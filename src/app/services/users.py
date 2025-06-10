from __future__ import annotations

from typing import TYPE_CHECKING

from src import core
from src.app import models, repositories, schemas

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Users(
    core.services.BaseCRUD[
        schemas.users.Create,
        schemas.users.Read,
        schemas.users.Update,
        schemas.users.Filters,
        schemas.users.SortParams,
        models.User,
    ],
):
    def __init__(self):
        self.repo = repositories.Users()
        super().__init__(
            self.repo,
            create_schema=schemas.users.Create,
            read_schema=schemas.users.Read,
            update_schema=schemas.users.Update,
            filters_schema=schemas.users.Filters,
        )

    async def read_by_name(self, uow: UnitOfWork, name: str) -> schemas.users.Read:
        user = await self.repo.read_by_name(uow, name)

        if not user:
            raise core.services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"name={name}",
            )

        return await self._validate_data(user)

    async def get_or_create_user(
        self,
        uow: UnitOfWork,
        user_data: schemas.users.Create,
    ) -> schemas.users.Read:
        try:
            return await self.read_by_name(uow, user_data.name)
        except core.services.exceptions.EntityNotFoundError:
            return await self.create(
                uow,
                user_data,
            )
