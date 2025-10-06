from src import core
from src.app import models


class BalanceOperations(core.repositories.sqlalchemy.BaseCRUD[models.BalanceOperation]):
    def __init__(self):
        super().__init__(models.BalanceOperation)
