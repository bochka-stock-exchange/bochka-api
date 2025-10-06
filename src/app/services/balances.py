from src import core
from src.app import models, repositories, schemas


class Balances(
    core.services.BaseCRUD[
        schemas.balance.Create,
        schemas.balance.Read,
        schemas.balance.Update,
        schemas.balance.Filters,
        schemas.balance.SortParams,
        models.Balance,
    ],
):
    def __init__(self):
        self.repo = repositories.Balances()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.balance.Create,
            read_schema=schemas.balance.Read,
            update_schema=schemas.balance.Update,
            filters_schema=schemas.balance.Filters,
        )
