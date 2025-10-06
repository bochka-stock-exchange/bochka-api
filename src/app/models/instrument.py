from typing import TYPE_CHECKING

from sqlalchemy import UUID, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.balance import Balance
    from src.app.models.balance_operation import BalanceOperation
    from src.app.models.order import Order, Transaction


class Instrument(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "instruments"
    repr_cols = ("ticker", "name")

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid7)
    ticker: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(255))

    balances: Mapped[list["Balance"]] = relationship("Balance", back_populates="instrument")
    balance_operations: Mapped[list["BalanceOperation"]] = relationship(
        "BalanceOperation",
        back_populates="instrument",
    )
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
