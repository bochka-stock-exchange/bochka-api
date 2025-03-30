from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from src.core import repositories

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(repositories.exceptions.EntityCreateError)
    def handle_entity_create_error(
        request: Request, exc: repositories.exceptions.EntityCreateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(repositories.exceptions.EntityReadError)
    def handle_entity_read_error(
        request: Request, exc: repositories.exceptions.EntityReadError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(repositories.exceptions.EntityUpdateError)
    def handle_entity_update_error(
        request: Request, exc: repositories.exceptions.EntityUpdateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(repositories.exceptions.EntityDeleteError)
    def handle_entity_delete_error(
        request: Request, exc: repositories.exceptions.EntityDeleteError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )