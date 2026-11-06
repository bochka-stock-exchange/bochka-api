from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from src import core
from src.app import schemas
from src.app.api.dependencies import services, uow
from src.app.models import UserRole

settings = core.config.get_settings()

token_prefix = getattr(settings, "TOKEN_PREFIX", "TOKEN")

authorization_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description=f"Authorization: {token_prefix} <api_key>",
)

Token = Annotated[
    str | None,
    Security(authorization_header),
]


async def get_current_user(
    auth_service: services.Auth,
    uow: uow.Postgres,
    token: Token,
) -> schemas.users.Read:
    if not token:
        raise core.services.exceptions.AuthenticationError("Token is missing")

    if not token.startswith(token_prefix):
        raise core.services.exceptions.AuthenticationError(
            f"Invalid token format: {token}. Should be: {token_prefix} <api_key>",
        )

    api_key = token[len(token_prefix) + 1 :].strip()

    return await auth_service.read_user_by_token(uow, api_key)


CurrentUser = Annotated[schemas.users.Read, Depends(get_current_user)]


def get_admin_user(
    current_user: CurrentUser,
) -> schemas.users.Read:
    if current_user.role != UserRole.ADMIN:
        raise core.services.exceptions.PermissionDeniedError(
            f"{UserRole.ADMIN} role required. Your role: {current_user.role}",
        )
    return current_user


AdminUser = Annotated[schemas.users.Read, Depends(get_admin_user)]
