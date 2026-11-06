import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

from src import core

from . import instruments as instrument_schemas

BalanceAmount = Annotated[int, Field(ge=0)]

BalanceOperationAmount = Annotated[int, Field(gt=0)]


class CreateRequest(BaseModel):
    user_id: UUID
    amount: BalanceOperationAmount
    ticker: instrument_schemas.Ticker


class OperationSuccess(BaseModel):
    success: bool = True


class Base(BaseModel):
    user_id: UUID
    amount: BalanceAmount
    instrument_id: UUID


class Create(Base):
    pass


class Update(BaseModel):
    amount: BalanceAmount | None


class Read(Base):
    id: Annotated[UUID, Field(exclude=True)]
    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    user_id: list[UUID] | UUID | None = None
    ticker: list[instrument_schemas.Ticker] | instrument_schemas.Ticker | None = None
    amount_from: BalanceAmount | None = None
    amount_to: BalanceAmount | None = None


class SortFields(enum.StrEnum):
    TICKER = "ticker"
    AMOUNT = "amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class BalanceReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass


class Response(RootModel[dict[instrument_schemas.Ticker, BalanceAmount]]):
    root: dict[instrument_schemas.Ticker, BalanceAmount]

    model_config = ConfigDict(
        json_schema_extra={"example": {"MEMCOIN": 0, "DODGE": 100500, "BITCOIN": 42}},
    )
