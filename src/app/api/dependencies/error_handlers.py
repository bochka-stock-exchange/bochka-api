from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse

from src import core

from . import exceptions


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(exceptions.NotEnoughFundsError)
    def handle_not_enough_funds(
        request: Request, exc: exceptions.NotEnoughFundsError
    ) -> ORJSONResponse:
        return core.error_handlers.make_error_response(
            str(exc),
            "User don't have enough funds",
            "not_enough_funds",
            status.HTTP_400_BAD_REQUEST,
        )
