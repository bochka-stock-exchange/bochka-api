from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

import src.models as models
import src.services as services
from src.db import db_manager
from src.schemas.user import UserRead

Session = Annotated[AsyncSession, Depends(db_manager.get_session)]

UsersService = Annotated[services.UsersService, Depends()]
InstrumentsService = Annotated[services.InstrumentsService, Depends()]

authorization_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="Authorization: TOKEN <api_key>",
)

Token = Annotated[
    Optional[str],
    Security(authorization_header),
]


async def get_current_user(
    service: UsersService,
    session: Session,
    token: Token,
) -> UserRead:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отсутствует")

    prefix = "TOKEN "

    if not token.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный формат токена"
        )

    api_key = token[len(prefix) :].strip()
    user = await service.get_by_api_key(session, api_key)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен")

    return user


CurrentUser = Annotated[UserRead, Depends(get_current_user)]


async def get_admin_user(
    current_user: CurrentUser,
) -> UserRead:
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Требуется роль Администратор")
    return current_user


AdminUser = Annotated[UserRead, Depends(get_admin_user)]
