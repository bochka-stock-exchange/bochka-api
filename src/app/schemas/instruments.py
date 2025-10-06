import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core

Ticker = Annotated[str, Field(pattern="^[A-Z]{2,10}$")]
InstrumentName = Annotated[str, Field(max_length=255)]


class Base(BaseModel):
    ticker: Ticker
    name: InstrumentName


class Create(Base):
    pass


class Update(BaseModel):
    name: InstrumentName | None = None


class Read(Base):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class ReadTicker(BaseModel):
    id: UUID
    ticker: Ticker
    model_config = ConfigDict(from_attributes=True)


class Delete(BaseModel):
    success: bool = True


class CreateResponse(BaseModel):
    success: bool = True


class Filters(core.schemas.BaseFilters):
    pass


class SortFields(enum.StrEnum):
    TICKER = "ticker"
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class ReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
