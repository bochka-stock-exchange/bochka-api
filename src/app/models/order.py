import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Enum, ForeignKey, Integer, String
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


class Order(core.models.Base):
    __tablename__ = "orders"
    repr_cols = ("id", "user_id", "ticker")

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.NEW,
        nullable=False,
    )
    direction: Mapped[Direction] = mapped_column(Enum(Direction), nullable=False)
    ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker"),
        nullable=False,
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    filled: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="orders")


class Transaction(core.models.Base):
    __tablename__ = "transactions"
    repr_cols = ("id", "ticker", "amount")

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="transactions")
