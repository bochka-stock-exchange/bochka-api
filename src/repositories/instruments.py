import src.models as models
import src.repositories as repositories


class Instruments(repositories.SQLAlchemyCRUD[models.Instrument]):
    def __init__(self):
        super().__init__(models.Instrument)
