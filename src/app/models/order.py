import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class OrderType(enum.StrEnum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(enum.StrEnum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class Direction(enum.StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class Order(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "orders"
    repr_cols = ("id", "status", "direction", "order_type", "qty", "locked_amount")

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    status: Mapped[OrderStatus] = mapped_column(default=OrderStatus.NEW)
    direction: Mapped[Direction]
    order_type: Mapped[OrderType]

    qty: Mapped[int]
    filled: Mapped[int] = mapped_column(default=0)

    price: Mapped[int | None] = mapped_column(default=None)
    locked_amount: Mapped[int] = mapped_column(default=0)

    user_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
    )
    instrument_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("instruments.id"))

    user: Mapped["User"] = relationship("User", back_populates="orders", lazy="selectin")
    instrument: Mapped["Instrument"] = relationship(
        "Instrument", back_populates="orders", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("qty >= 1", name="check_qty_constraint"),
        CheckConstraint("locked_amount >= 0", name="check_locked_amount_constraint"),
    )
