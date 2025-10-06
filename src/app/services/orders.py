from src import core
from src.app import models, repositories, schemas


class Orders(
    core.services.BaseCRUD[
        schemas.orders.Create,
        schemas.orders.Read,
        schemas.orders.Update,
        schemas.orders.Filters,
        schemas.orders.SortParams,
        models.Order,
    ]
):
    def __init__(self):
        self.repo = repositories.Orders()
        super().__init__(
            self.repo,
            create_schema=schemas.orders.Create,
            read_schema=schemas.orders.Read,
            update_schema=schemas.orders.Update,
            filters_schema=schemas.orders.Filters,
        )
