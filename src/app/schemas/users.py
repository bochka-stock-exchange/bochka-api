import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.app import models

settings = core.config.get_settings()

UserName = Annotated[str, Field(min_length=3, max_length=255)]


class Base(BaseModel):
    name: UserName


class Create(Base):
    pass


class Update(BaseModel):
    name: UserName | None = None


class Read(Base):
    id: UUID
    role: models.UserRole

    model_config = ConfigDict(from_attributes=True)


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


class Auth(Base):
    id: UUID
    role: models.UserRole
    api_key: str
