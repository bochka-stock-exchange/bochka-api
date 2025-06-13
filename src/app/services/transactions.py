from src import core
from src.app import models, repositories, schemas


class Transactions(
    core.services.BaseCRUD[
        schemas.transactions.Create,
        schemas.transactions.Read,
        schemas.transactions.Update,
        schemas.transactions.Filters,
        schemas.transactions.SortParams,
        models.Transaction,
    ]
):
    def __init__(self):
        self.repo = repositories.Transactions()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.transactions.Create,
            read_schema=schemas.transactions.Read,
            update_schema=schemas.transactions.Update,
            filters_schema=schemas.transactions.Filters,
        )
