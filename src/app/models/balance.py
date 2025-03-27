import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class OperationType(enum.StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class Balance(core.models.Base):
    __tablename__ = "balances"

    repr_cols = ("user_id", "ticker", "amount")

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker"),
        primary_key=True,
    )
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="balances")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="balances")


class BalanceOperation(core.models.Base):
    __tablename__ = "balance_operations"
    repr_cols = ("id", "user_id", "ticker")

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="operations")
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="balance_operations",
    )
