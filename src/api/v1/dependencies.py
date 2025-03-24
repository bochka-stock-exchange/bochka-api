from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db_manager
from src.models.user import UserRole
from src.schemas.user import UserRead
from src.services.instrument import InstrumentService
from src.services.user import UserService

UserServiceDependency = Annotated[UserService, Depends()]
InstrumentServiceDependency = Annotated[InstrumentService, Depends()]
SessionDependency = Annotated[AsyncSession, Depends(db_manager.get_session)]


authorization_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="Authorization: TOKEN <api_key>",
)


async def get_current_user(
    service: UserServiceDependency,
    session: SessionDependency,
    token: Annotated[Optional[str], Security(authorization_header)],
) -> UserRead:
    """
    Authenticates the request using the provided API token and returns the corresponding user.
    
    Validates that the token is provided and starts with "TOKEN ". Extracts the API key and retrieves the user from the database using the user service and session. Raises an HTTPException with a 401 status code if the token is missing, improperly formatted, or does not match any user.
    """
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


async def get_admin_user(
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """
    Validates that the current user has administrative privileges.
    
    This function checks if the authenticated user, provided through dependency injection, has the admin role.
    If the user does not have admin rights, an HTTPException with a 403 status is raised.
    Otherwise, the function returns the authenticated user.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Требуется роль Администратор")
    return current_user
