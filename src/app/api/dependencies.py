from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from src import core
from src.app import schemas, services
from src.app.models import UserRole

settings = core.config.get_settings()


def get_uow_factory(
    *,
    use_postgres: bool = True,
) -> Callable[[], AsyncGenerator[core.UnitOfWork]]:
    async def _get_uow() -> AsyncGenerator[core.UnitOfWork]:
        async with core.UnitOfWork(use_postgres=use_postgres) as uow:
            yield uow

    return _get_uow


UoWPostgres = Annotated[core.UnitOfWork, Depends(get_uow_factory(use_postgres=True))]

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
    uow: UoWPostgres,
    token: Token,
) -> schemas.users.Read:
    if not token:
        raise core.services.exceptions.AuthenticationError("Token is missing")

    if not token.startswith(token_prefix):
        raise core.services.exceptions.AuthenticationError(
            f"Invalid token format: {token}. Should be: {token_prefix} <api_key>"
        )

    api_key = token[len(token_prefix) + 1 :].strip()
    user = await service.get_by_api_key(uow, api_key)
    if not user:
        raise core.services.exceptions.AuthenticationError(f"Invalid token: {token}")

    return user


CurrentUser = Annotated[schemas.users.Read, Depends(get_current_user)]


def get_admin_user(
    current_user: CurrentUser,
) -> schemas.users.Read:
    if current_user.role != UserRole.ADMIN:
        raise core.services.exceptions.PermissionDeniedError(
            f"{UserRole.ADMIN} role required. Your role: {current_user.role}"
        )
    return current_user


AdminUser = Annotated[schemas.users.Read, Depends(get_admin_user)]

Pagination = Annotated[core.schemas.PaginationParams, Depends()]
