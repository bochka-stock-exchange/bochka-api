from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class Balance(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "balances"
    repr_cols = ("user_id", "ticker", "amount")

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    user_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("users.id"))
    instrument_id: Mapped[Uuid] = mapped_column(Uuid, ForeignKey("instruments.id"))
    amount: Mapped[int] = mapped_column(default=0)

    user: Mapped["User"] = relationship("User", back_populates="balances")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="balances")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_balance_amount_non_negative"),
        Index(
            "uq_balances_user_instrument_active",
            user_id,
            instrument_id,
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
