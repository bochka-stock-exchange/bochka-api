from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy import Row, Uuid, select

from src import core
from src.app import models

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Instruments(core.repositories.sqlalchemy.BaseCRUD[models.Instrument]):
    def __init__(self):
        super().__init__(models.Instrument)

    async def get_all_instruments(self, uow: UnitOfWork) -> Sequence[Row[tuple[Uuid, str]]]:
        try:
            session = uow.postgres_session

            instruments_query = select(models.Instrument.id, models.Instrument.ticker).where(
                models.Instrument.deleted_at.is_(None)
            )
            instruments = await session.execute(instruments_query)

            return instruments.all()
        except Exception:
            raise

    async def read_by_ticker(
        self, uow: UnitOfWork, ticker: str, *, include_deleted: bool = False
    ) -> models.Instrument | None:
        try:
            query = select(models.Instrument).filter_by(ticker=ticker)

            if not include_deleted:
                query = query.where(models.Instrument.deleted_at.is_(None))

            return await uow.postgres_session.scalar(query)
        except Exception:
            raise
