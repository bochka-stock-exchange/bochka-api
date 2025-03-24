import src.models as models
import src.repositories as repositories


class InstrumentsRepository(repositories.SQLAlchemyRepository[models.Instrument]):
    def __init__(self):
        super().__init__(models.Instrument)
