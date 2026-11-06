from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src import core
from src.app.utils.orderbook import OrderBook

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork


@core.utils.decorators.Singleton
class OrderBookManager:
    def __init__(self):
        self._order_books: dict[UUID, OrderBook] = {}

    async def get_order_book(
        self,
        uow: UnitOfWork,
        instrument_id: UUID,
        pagination: core.schemas.PaginationParams | None = None,
        *,
        refresh: bool = False,
    ) -> OrderBook:
        if instrument_id not in self._order_books or refresh:
            order_book = OrderBook(instrument_id)
            await order_book.load_from_db(uow, pagination)
            self._order_books[instrument_id] = order_book
        return self._order_books[instrument_id]

    def clear_order_book(self, instrument_id: UUID) -> None:
        self._order_books.pop(instrument_id, None)


def get_order_book_manager() -> OrderBookManager:
    return OrderBookManager()
