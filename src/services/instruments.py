import src.repositories as repositories
import src.services as services
from src.schemas.instrument import InstrumentCreate, InstrumentRead


class InstrumentsService(services.BaseService[InstrumentCreate, InstrumentRead, InstrumentCreate]):
    def __init__(self):
        repo = repositories.InstrumentsRepository()
        super().__init__(
            repo,
            create_schema=InstrumentCreate,
            read_schema=InstrumentRead,
            update_schema=InstrumentCreate,
        )
