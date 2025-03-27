from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

from src import core
from src.app import api

settings = core.config.get_settings()


def add_middlewares(application: FastAPI) -> None:
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not settings.DEBUG:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOW_HOSTS)


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    app.include_router(api.v1.router, prefix=settings.API_PREFIX)

    return app
