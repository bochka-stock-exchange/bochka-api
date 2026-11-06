from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from jose import JWTError, jwt

from src import core

if TYPE_CHECKING:
    from src.core.uow import UnitOfWork

from src.app import schemas, services

settings = core.config.get_settings()


class Authentication:
    def __init__(
        self,
    ):
        self.context = {}
        self.logger = logging.getLogger(f"services.{self.__class__.__name__.lower()}")

    async def auth_user(
        self,
        uow: UnitOfWork,
        create_schema: schemas.users.Create,
    ) -> schemas.users.Auth:
        user = await services.Users().get_or_create_user(uow, create_schema)
        token = self.encode_token({"user_id": str(user.id)})
        return schemas.users.Auth(id=user.id, name=user.name, role=user.role, api_key=token)

    async def read_user_by_token(self, uow: UnitOfWork, token: str) -> schemas.users.Read:
        user_data = self.decode_token(token)
        return await services.Users().read_by_id(uow, user_data["user_id"])

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        except JWTError:
            raise core.services.exceptions.AuthenticationError("Invalid credentials") from None

    @staticmethod
    def encode_token(data: dict) -> str:
        return jwt.encode(data, settings.SECRET_KEY, algorithm="HS256")
