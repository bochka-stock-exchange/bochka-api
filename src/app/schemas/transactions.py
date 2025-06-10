import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src import core

from . import instruments as instrument_schemas

TransactionAmount = Annotated[int, Field(gt=0)]
TransactionPrice = Annotated[int, Field(ge=0)]


class TransactionsPaginationParams(core.schemas.PaginationParams):
    limit: Annotated[int, Field(ge=1, le=100)] = 10


class Base(BaseModel):
    amount: TransactionAmount
    price: TransactionPrice


class Create(Base):
    instrument_id: UUID


class Update(BaseModel):
    pass


class Read(Base):
    id: UUID
    created_at: Annotated[datetime, Field(serialization_alias="timestamp")]

    instrument: Annotated[instrument_schemas.Read, Field(exclude=True)]

    @computed_field
    @property
    def ticker(self) -> instrument_schemas.Ticker:
        return self.instrument.ticker

    model_config = ConfigDict(from_attributes=True)


class CreateResponse(BaseModel):
    success: bool = True


class Filters(core.schemas.BaseFilters):
    instrument_id: list[UUID] | UUID | None = None


class SortFields(enum.StrEnum):
    AMOUNT = "amount"
    PRICE = "price"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class ReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
