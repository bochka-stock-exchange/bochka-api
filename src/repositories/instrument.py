from src.models.instrument import Instrument
from src.repositories.base import SQLAlchemyRepository


class InstrumentRepository(SQLAlchemyRepository[Instrument]):
    def __init__(self):
        super().__init__(Instrument)
