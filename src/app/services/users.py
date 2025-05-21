from uuid_v7.base import uuid7

from src import core
from src.app import models, repositories, schemas


class Users(
    core.services.BaseCRUD[
        schemas.users.Create,
        schemas.users.Read,
        schemas.users.Update,
        schemas.users.Filters,
        schemas.users.SortParams,
        models.User,
    ]
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

    @staticmethod
    def _prepare_data(data: dict) -> dict:
        data["api_key"] = "key-" + str(uuid7())
        return data

    async def get_by_api_key(
        self,
        uow: core.UnitOfWork,
        api_key: str,
    ) -> schemas.users.Read | None:
        user_data = await self.repo.get_by_api_key(uow, api_key)

        return self.read_schema.model_validate(user_data) if user_data else None
