import base64
import enum
from typing import Annotated
from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import BaseModel, ConfigDict, Field, computed_field

from src import core
from src.app import models

settings = core.config.get_settings()


class Base(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=255)]


class Create(Base):
    pass


class Update(Base):
    pass


class Read(Base):
    id: UUID
    role: models.UserRole

    @computed_field
    @property
    def api_key(self) -> str:
        # Генерируем ключ для шифрования на основе SECRET_KEY
        # SECRET_KEY должен быть длиной 32 url-safe base64-encoded bytes
        # Если ваш SECRET_KEY не подходит, можно сделать так:
        key = base64.urlsafe_b64encode(settings.SECRET_KEY.ljust(32)[:32].encode())

        cipher_suite = Fernet(key)

        encrypted = cipher_suite.encrypt(str(self.id).encode())

        return encrypted.decode()

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Filters(core.schemas.BaseFilters):
    pass


class SortFields(enum.StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class ReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
