import src.repositories as repositories
import src.schemas as schemas
import src.services as services


class Instruments(
    services.BaseCRUD[schemas.InstrumentCreate, schemas.InstrumentRead, schemas.InstrumentCreate]
):
    def __init__(self):
        repo = repositories.Instruments()
        super().__init__(
            repo,
            create_schema=schemas.InstrumentCreate,
            read_schema=schemas.InstrumentRead,
            update_schema=schemas.InstrumentCreate,
        )
