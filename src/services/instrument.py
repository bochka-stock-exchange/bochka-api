from src.repositories.instrument import InstrumentRepository
from src.schemas.instrument import InstrumentCreate, InstrumentRead
from src.services.base import BaseService


class InstrumentService(BaseService[InstrumentCreate, InstrumentRead, InstrumentCreate]):
    def __init__(self):
        repo = InstrumentRepository()
        super().__init__(
            repo,
            create_schema=InstrumentCreate,
            read_schema=InstrumentRead,
            update_schema=InstrumentCreate,
        )
