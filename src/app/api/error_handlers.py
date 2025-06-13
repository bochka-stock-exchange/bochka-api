from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src import core
from src.app import services


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(services.exceptions.InsufficientBalanceError)
    def handle_not_enough_funds(
        request: Request, exc: services.exceptions.InsufficientBalanceError
    ) -> ORJSONResponse:
        return core.error_handlers.make_error_response(
            str(exc),
            "Not enough funds",
            "not_enough_funds",
            status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(services.exceptions.OrderRejectedError)
    def handle_market_order_reject(
        request: Request, exc: services.exceptions.OrderRejectedError
    ) -> ORJSONResponse:
        return core.error_handlers.make_error_response(
            str(exc),
            "Market order not fully filled",
            "market_order_not_filled",
            status.HTTP_400_BAD_REQUEST,
        )
