from collections.abc import Sequence

from sqlalchemy import UUID, Row, select

from src import core
from src.app import models


class Instruments(core.repositories.sqlalchemy.BaseCRUD[models.Instrument]):
    def __init__(self):
        super().__init__(models.Instrument)

    @staticmethod
    async def get_all_instruments(uow: core.UnitOfWork) -> Sequence[Row[tuple[UUID, str]]]:
        session = uow.postgres_session

        instruments_query = select(models.Instrument.id, models.Instrument.ticker).where(
            models.Instrument.deleted_at.is_(None)
        )
        instruments = await session.execute(instruments_query)

        return instruments.all()

    @staticmethod
    async def read_by_ticker(
        uow: core.UnitOfWork, ticker: str, *, include_deleted: bool = False
    ) -> models.Instrument | None:
        query = select(models.Instrument).filter_by(ticker=ticker)

        if not include_deleted:
            query = query.where(models.Instrument.deleted_at.is_(None))

        return await uow.postgres_session.scalar(query)
