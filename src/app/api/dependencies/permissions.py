import base64
from typing import Annotated
from uuid import UUID

import cryptography.fernet
from cryptography.fernet import Fernet
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


def decrypt_api_key(encrypted_api_key: str) -> UUID:
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.ljust(32)[:32].encode())
    cipher_suite = Fernet(key)

    decrypted = cipher_suite.decrypt(encrypted_api_key.encode())
    return UUID(decrypted.decode())


async def get_current_user(
    service: services.Users,
    uow: uow.Postgres,
    token: Token,
) -> schemas.users.Read:
    if not token:
        raise core.services.exceptions.AuthenticationError("Token is missing")

    if not token.startswith(token_prefix):
        raise core.services.exceptions.AuthenticationError(
            f"Invalid token format: {token}. Should be: {token_prefix} <api_key>"
        )

    api_key = token[len(token_prefix) + 1 :].strip()

    try:
        user_id = decrypt_api_key(api_key)
    except cryptography.fernet.InvalidToken as err:
        raise core.services.exceptions.AuthenticationError(f"Invalid token: {token}") from err

    user = await service.read_by_id(uow, user_id)
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
