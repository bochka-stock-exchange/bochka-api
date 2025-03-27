from src import core
from src.app import models


class Instruments(core.repositories.sqlalchemy.BaseCRUD[models.Instrument]):
    def __init__(self):
        super().__init__(models.Instrument)
