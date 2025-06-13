from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class Balance(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "balances"
    repr_cols = ("amount", "user_id", "instrument_id")

    amount: Mapped[int] = mapped_column(default=0)

    locked_amount: Mapped[int] = mapped_column(default=0)

    user_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("users.id"), primary_key=True)
    instrument_id: Mapped[Uuid] = mapped_column(
        Uuid, ForeignKey("instruments.id"), primary_key=True
    )

    user: Mapped["User"] = relationship("User", back_populates="balances", lazy="selectin")
    instrument: Mapped["Instrument"] = relationship(
        "Instrument", back_populates="balances", lazy="selectin"
    )

    __table_args__ = (CheckConstraint("amount >= 0", name="check_balance_amount_non_negative"),)
