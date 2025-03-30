from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from src.core import services


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(services.exceptions.EntityNotFoundError)
    def handle_entity_not_found(
        request: Request, exc: services.exceptions.EntityNotFoundError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=404,
            content={"message": str(exc)},
        )

    @app.exception_handler(services.exceptions.EntityCreateError)
    def handle_entity_create_error(
        request: Request, exc: services.exceptions.EntityCreateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(services.exceptions.EntityReadError)
    def handle_entity_read_error(
        request: Request, exc: services.exceptions.EntityReadError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(services.exceptions.EntityUpdateError)
    def handle_entity_update_error(
        request: Request, exc: services.exceptions.EntityUpdateError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(services.exceptions.EntityDeleteError)
    def handle_entity_delete_error(
        request: Request, exc: services.exceptions.EntityDeleteError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @app.exception_handler(services.exceptions.PermissionDeniedError)
    def handle_permission_denied_error(
        request: Request, exc: services.exceptions.PermissionDeniedError
    ) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=403,
            content={"message": str(exc)},
        )
