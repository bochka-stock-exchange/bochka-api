from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.api.v1 import router as api_v1_router
from src.config import get_settings

settings = get_settings()


def add_middlewares(application: FastAPI) -> None:
    """
    Configure middlewares for the FastAPI application.
    
    Adds CORS middleware using settings-defined origins, credential support, and
    permissive HTTP methods and headers. In non-debug mode, also adds trusted host
    middleware to restrict requests to allowed hosts.
    """
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
    """
    Creates and configures a FastAPI application instance.
    
    The application is initialized with settings for debug mode, title, description,
    and version. It also includes the API router under the specified prefix.
    
    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    app = FastAPI(
        debug=settings.DEBUG,
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )

    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return app
