from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core
from src.app.models.balance import Balance, BalanceOperation
from src.app.models.order import Order, Transaction


class Instrument(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "instruments"
    repr_cols = ("ticker", "name")

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

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
