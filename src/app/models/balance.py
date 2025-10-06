from typing import TYPE_CHECKING

from sqlalchemy import UUID, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class Balance(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "balances"
    repr_cols = ("user_id", "ticker", "amount")

    __table_args__ = (CheckConstraint("amount >= 0", name="check_balance_amount_non_negative"),)

    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"), primary_key=True)
    instrument_id: Mapped[UUID] = mapped_column(
        UUID, ForeignKey("instruments.id"), primary_key=True
    )
    amount: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship("User", back_populates="balances")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="balances")
