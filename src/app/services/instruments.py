from src import core
from src.app import models, repositories, schemas
from src.core import services


class Instruments(
    core.services.BaseCRUD[
        schemas.instruments.Create,
        schemas.instruments.Read,
        schemas.instruments.Update,
        schemas.instruments.Filters,
        schemas.instruments.SortParams,
        models.Instrument,
    ],
):
    def __init__(self):
        self.repo = repositories.Instruments()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.instruments.Create,
            read_schema=schemas.instruments.Read,
            update_schema=schemas.instruments.Update,
            filters_schema=schemas.instruments.Filters,
        )

    async def get_all_instruments(
        self, uow: core.UnitOfWork
    ) -> list[schemas.instruments.ReadTicker]:
        instruments = await self.repo.get_all_instruments(uow)

        return [
            schemas.instruments.ReadTicker.model_validate(instrument) for instrument in instruments
        ]

    async def read_by_ticker(
        self, uow: core.UnitOfWork, ticker: str, *, include_deleted: bool = False
    ) -> schemas.instruments.Read:
        instrument = await self.repo.read_by_ticker(uow, ticker, include_deleted=include_deleted)

        if not instrument:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"ticker: {ticker}",
            )

        return await self._validate_data(instrument)

    async def delete_by_ticker(self, uow: core.UnitOfWork, ticker: str) -> bool:
        instrument = await self.repo.read_by_ticker(uow, ticker)

        if not instrument:
            raise services.exceptions.EntityNotFoundError(
                self.__class__.__name__,
                f"ticker: {ticker}",
            )

        return await self.delete_by_id(uow, instrument.id)
