from src.models.instrument import Instrument
from src.repositories.base import SQLAlchemyRepository


class InstrumentRepository(SQLAlchemyRepository[Instrument]):
    def __init__(self):
        """
        Initializes the InstrumentRepository instance.
        
        Calls the superclass constructor with the Instrument model to establish the
        repository context for managing Instrument entities.
        """
        super().__init__(Instrument)
