from uuid import UUID

from src.core.services.exceptions import ServiceError


class InsufficientBalanceError(ServiceError):
    """Exception class for not enough funds in balance."""

    def __init__(self, user_id: UUID, ticker: str):
        super().__init__(f"User <{user_id}> has not enough ({ticker})")


class OrderRejectedError(ServiceError):
    """Raised when Market order can't be executed"""

    def __init__(self, order_id: UUID, qty: int, remaining_qty: int):
        fill_qty = qty - remaining_qty
        super().__init__(
            f"Market order <{order_id}> not filled, could be filled up to: <{fill_qty}/{qty}>",
        )
