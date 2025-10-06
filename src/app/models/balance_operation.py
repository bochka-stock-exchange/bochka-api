import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, CheckConstraint, ForeignKey
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.instrument import Instrument
    from src.app.models.user import User


class OperationType(enum.StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class BalanceOperation(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "balance_operations"
    repr_cols = ("id", "user_id", "ticker")

    __table_args__ = (CheckConstraint("amount > 0", name="check_operation_amount_positive"),)

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid7)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"))

    instrument_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("instruments.id"))

    amount: Mapped[int]
    operation_type: Mapped[OperationType] = mapped_column(
        SQLAlchemyEnum(
            OperationType,
            name="operationtype",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )

    user: Mapped["User"] = relationship("User", back_populates="operations")
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="balance_operations",
    )
