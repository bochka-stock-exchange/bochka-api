from src.repositories.instrument import InstrumentRepository
from src.schemas.instrument import InstrumentCreate, InstrumentRead
from src.services.base import BaseService


class InstrumentService(BaseService[InstrumentCreate, InstrumentRead, InstrumentCreate]):
    def __init__(self):
        """
        Initialize an InstrumentService instance.
        
        Instantiates an InstrumentRepository and configures the service with the schemas for creating, reading, and updating instruments, using InstrumentCreate for both creation and updating.
        """
        repo = InstrumentRepository()
        super().__init__(
            repo,
            create_schema=InstrumentCreate,
            read_schema=InstrumentRead,
            update_schema=InstrumentCreate,
        )
