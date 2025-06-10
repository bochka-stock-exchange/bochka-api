from src import core
from src.app import models


class Transactions(core.repositories.sqlalchemy.BaseCRUD[models.Transaction]):
    def __init__(self):
        super().__init__(models.Transaction)
