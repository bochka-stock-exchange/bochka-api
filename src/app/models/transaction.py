from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument


class Transaction(core.models.sqlalchemy.Base):
    __tablename__ = "transactions"
    repr_cols = ("id", "ticker", "amount")
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_transaction_amount_positive"),
        CheckConstraint("price >= 0", name="check_price_transaction_non_negative"),
    )

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    instrument_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("instruments.id"))
    amount: Mapped[int]
    price: Mapped[int]

    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="transactions",
        lazy="selectin",
    )
