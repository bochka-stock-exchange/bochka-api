import enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src import core


class Base(BaseModel):
    ticker: Annotated[str, Field(pattern="^[A-Z]{2,10}$")]
    name: Annotated[str, Field(max_length=255)]


class Create(Base):
    pass


class Update(Base):
    pass


class Read(Base):
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
