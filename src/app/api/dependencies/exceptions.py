from uuid import UUID


class NotEnoughFundsError(Exception):
    """Exception class for not enough funds in balance."""

    def __init__(self, user_id: UUID, ticker: str):
        super().__init__(f"User ({user_id}) don't have enough funds ({ticker})")
