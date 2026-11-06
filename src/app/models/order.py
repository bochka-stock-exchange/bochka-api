import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Uuid
from sqlalchemy import Enum as SQLAlchemyEnum
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
    repr_cols = ("id", "user_id", "status", "direction", "qty", "price", "order_type", "filled")

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[Uuid] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLAlchemyEnum(
            OrderStatus,
            name="orderstatus",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=OrderStatus.NEW,
    )
    direction: Mapped[Direction] = mapped_column(
        SQLAlchemyEnum(
            Direction,
            name="orderdirection",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
    )

    instrument_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("instruments.id"))

    qty: Mapped[int]
    price: Mapped[int | None] = mapped_column(default=None)

    order_type: Mapped[OrderType] = mapped_column(
        SQLAlchemyEnum(
            OrderType,
            name="ordertype",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
    )

    locked_money_amount: Mapped[int | None] = mapped_column(default=None)
    locked_instrument_amount: Mapped[int | None] = mapped_column(default=None)

    filled: Mapped[int | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="orders",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("qty >= 1", name="check_qty_constraint"),
        CheckConstraint(
            "(order_type = 'LIMIT' AND filled >= 0) OR (order_type = 'MARKET' AND filled IS NULL)",
            name="check_filled_for_order_type",
        ),
        CheckConstraint(
            "(order_type = 'LIMIT' AND price > 0) OR (order_type = 'MARKET' AND price IS NULL)",
            name="check_price_for_order_type",
        ),
        CheckConstraint(
            """
                (
                    order_type = 'MARKET' AND
                    locked_money_amount IS NULL AND
                    locked_instrument_amount IS NULL
                ) OR (
                    order_type = 'LIMIT' AND (
                        (direction = 'BUY' AND
                        locked_money_amount IS NOT NULL AND locked_instrument_amount IS NULL) OR
                        (direction = 'SELL' AND
                        locked_instrument_amount IS NOT NULL AND locked_money_amount IS NULL)
                    )
                )
                """,
            name="check_lock_amounts",
        ),
    )
