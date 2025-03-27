import enum
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.balance import Balance, BalanceOperation
    from src.app.models.order import Order

settings = core.config.get_settings()


class UserRole(enum.StrEnum):
    USER = getattr(settings, "USER_ROLE", "USER")
    ADMIN = getattr(settings, "ADMIN_ROLE", "ADMIN")


class User(core.models.Base):
    __tablename__ = "users"
    repr_cols = ("id", "name", "role")

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    api_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    balances: Mapped[list["Balance"]] = relationship("Balance", back_populates="user")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    operations: Mapped[list["BalanceOperation"]] = relationship(
        "BalanceOperation",
        back_populates="user",
    )
