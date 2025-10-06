from src import core
from src.app import models
from src.core import UnitOfWork


class Orders(core.repositories.sqlalchemy.BaseCRUD[models.Order]):
    def __init__(self):
        super().__init__(models.Order)

    async def create(self, uow: UnitOfWork, data: dict) -> models.Order:
        data.pop("ticker")
        return await super().create(uow, data)
