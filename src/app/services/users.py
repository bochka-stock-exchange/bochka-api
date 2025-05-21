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
