from uuid import UUID

from sqlalchemy import func, select

from src import core
from src.app import models
from src.core import UnitOfWork


class Orders(core.repositories.sqlalchemy.BaseCRUD[models.Order]):
    def __init__(self):
        super().__init__(models.Order)

    async def create(self, uow: UnitOfWork, data: dict) -> models.Order:
        data.pop("ticker")
        return await super().create(uow, data)

    async def get_order_book_levels(
        self, uow: UnitOfWork, instrument_id: UUID, direction: models.OrderDirection, limit: int
    ) -> list[dict]:
        try:
            session = uow.postgres_session
            stmt = (
                select(
                    self.model.price,
                    func.sum(self.model.qty - self.model.filled).label("total_qty"),
                )
                .where(self.model.instrument_id == instrument_id)
                .where(self.model.direction == direction)
                .where(
                    self.model.status.in_([
                        models.OrderStatus.NEW,
                        models.OrderStatus.PARTIALLY_EXECUTED,
                    ])
                )
                .where(self.model.order_type == models.OrderType.LIMIT)
                .group_by(self.model.price)
                .having(func.sum(self.model.qty - self.model.filled) > 0)
            )

            if direction == models.OrderDirection.BUY:
                stmt = stmt.order_by(self.model.price.desc())
            else:
                stmt = stmt.order_by(self.model.price.asc())

            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            rows = result.all()

            return [{"qty": row.total_qty, "price": row.price} for row in rows]
        except Exception as e:
            raise core.repositories.exceptions.DatabaseError(
                self.__class__.__name__,
                str(e),
            ) from e
