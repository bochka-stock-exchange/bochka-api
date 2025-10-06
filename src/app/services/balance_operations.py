from src import core
from src.app import models, repositories, schemas


class BalanceOperations(
    core.services.BaseCRUD[
        schemas.balance_operations.Create,
        schemas.balance_operations.Read,
        schemas.balance_operations.Update,
        schemas.balance_operations.Filters,
        schemas.balance_operations.SortParams,
        models.BalanceOperation,
    ],
):
    def __init__(self):
        self.repo = repositories.BalanceOperations()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.balance_operations.Create,
            read_schema=schemas.balance_operations.Read,
            update_schema=schemas.balance_operations.Update,
            filters_schema=schemas.balance_operations.Filters,
        )
