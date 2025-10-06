import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

from src import core

from . import instruments as instrument_schemas

BalanceOperationAmount = Annotated[int, Field(gt=0)]


class Base(BaseModel):
    user_id: UUID
    amount: BalanceOperationAmount
    instrument_id: UUID


class Create(Base):
    pass


class Update(BaseModel):
    amount: BalanceOperationAmount | None


class Read(Base):
    model_config = ConfigDict(from_attributes=True)


class Filters(core.schemas.BaseFilters):
    user_id: list[UUID] | UUID | None = None
    ticker: list[instrument_schemas.Ticker] | instrument_schemas.Ticker | None = None
    amount_from: BalanceOperationAmount | None = None
    amount_to: BalanceOperationAmount | None = None


class SortFields(enum.StrEnum):
    TICKER = "ticker"
    AMOUNT = "amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class BalanceReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass


BalanceAmount = Annotated[int, Field(ge=0)]


class Response(RootModel[dict[instrument_schemas.Ticker, BalanceAmount]]):
    root: dict[instrument_schemas.Ticker, BalanceAmount]

    model_config = ConfigDict(
        json_schema_extra={"example": {"MEMCOIN": 0, "DODGE": 100500, "BITCOIN": 42}}
    )
