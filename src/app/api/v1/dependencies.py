from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src import core
from src.app import schemas, services
from src.app.models import UserRole
from src.core.db import get_db_manager

settings = core.config.get_settings()
db_manager = get_db_manager()

DBSession = Annotated[AsyncSession, Depends(db_manager.get_session)]

UsersService = Annotated[services.Users, Depends()]
InstrumentsService = Annotated[services.Instruments, Depends()]


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
    service: UsersService,
    session: DBSession,
    token: Token,
) -> schemas.UserRead:
    if not token:
        raise core.exceptions.AuthenticationError("Token is missing")

    if not token.startswith(token_prefix):
        raise core.exceptions.AuthenticationError(
            f"Invalid token format: {token}. Should be: {token_prefix} <api_key>"
        )

    api_key = token[len(token_prefix) + 1 :].strip()
    user = await service.get_by_api_key(session, api_key)
    if not user:
        raise core.exceptions.AuthenticationError(f"Invalid token: {token}")

    return user


CurrentUser = Annotated[schemas.UserRead, Depends(get_current_user)]


def get_admin_user(
    current_user: CurrentUser,
) -> schemas.UserRead:
    if current_user.role != UserRole.ADMIN:
        raise core.exceptions.PermissionDeniedError(
            f"{UserRole.ADMIN} role required. Your role: {current_user.role}"
        )
    return current_user


AdminUser = Annotated[schemas.UserRead, Depends(get_admin_user)]
