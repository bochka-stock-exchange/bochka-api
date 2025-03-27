from src import core
from src.app import repositories, schemas


class Instruments(
    core.services.BaseCRUD[
        schemas.InstrumentCreate,
        schemas.InstrumentRead,
        schemas.InstrumentCreate,
    ],
):
    def __init__(self):
        self.repo = repositories.Instruments()
        super().__init__(
            self.repo,
            create_schema=schemas.InstrumentCreate,
            read_schema=schemas.InstrumentRead,
            update_schema=schemas.InstrumentCreate,
        )
