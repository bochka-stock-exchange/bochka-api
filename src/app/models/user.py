import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_v7.base import uuid7

from src import core

if TYPE_CHECKING:
    from src.app.models.balance import Balance
    from src.app.models.order import Order

settings = core.config.get_settings()


class UserRole(enum.StrEnum):
    USER = getattr(settings, "USER_ROLE", "USER")
    ADMIN = getattr(settings, "ADMIN_ROLE", "ADMIN")


class User(core.models.sqlalchemy.Base, core.models.sqlalchemy.SoftDelete):
    __tablename__ = "users"
    __soft_delete_cascades__ = ("balances", "orders")
    repr_cols = ("id", "name", "role")

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(
            UserRole,
            name="userrole",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=UserRole.USER,
    )

    balances: Mapped[list["Balance"]] = relationship("Balance", back_populates="user")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
