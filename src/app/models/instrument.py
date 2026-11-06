from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.balance import Balance
    from src.app.models.order import Order
    from src.app.models.transaction import Transaction


class Instrument(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "instruments"
    __soft_delete_cascades__ = ("balances", "orders", "transactions")
    repr_cols = ("ticker", "name")

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    ticker: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(255))

    balances: Mapped[list["Balance"]] = relationship("Balance", back_populates="instrument")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="instrument")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="instrument",
    )

    __table_args__ = (
        Index(
            "uq_instruments_ticker_active",
            ticker,
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
