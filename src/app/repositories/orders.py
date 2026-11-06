from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select

from src import core
from src.app import models

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


class Orders(core.repositories.sqlalchemy.BaseCRUD[models.Order]):
    def __init__(self):
        super().__init__(models.Order)

    async def sum_locked_money(self, uow: UnitOfWork, user_id: UUID) -> int:
        try:
            query = select(func.sum(models.Order.locked_money_amount)).where(
                models.Order.user_id == user_id,
                models.Order.direction == models.order.Direction.BUY,
                models.Order.status.in_([
                    models.order.OrderStatus.NEW,
                    models.order.OrderStatus.PARTIALLY_EXECUTED,
                ]),
                models.Order.locked_money_amount.is_not(None),
            )
            locked_money = await uow.postgres_session.scalar(query)
            return locked_money or 0
        except Exception:
            raise

    async def sum_locked_instrument(
        self, uow: UnitOfWork, user_id: UUID, instrument_id: UUID
    ) -> int:
        try:
            query = select(func.sum(models.Order.locked_instrument_amount)).where(
                models.Order.user_id == user_id,
                models.Order.direction == models.order.Direction.SELL,
                models.Order.instrument_id == instrument_id,
                models.Order.status.in_([
                    models.order.OrderStatus.NEW,
                    models.order.OrderStatus.PARTIALLY_EXECUTED,
                ]),
                models.Order.locked_instrument_amount.is_not(None),
                models.Order.deleted_at.is_(None),
            )
            locked_instrument = await uow.postgres_session.scalar(query)

            return locked_instrument or 0
        except Exception:
            raise
