import enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src import core
from src.app import models

from . import instruments as instrument_schemas

BalanceOperationAmount = Annotated[int, Field(gt=0)]


class Base(BaseModel):
    user_id: UUID
    amount: BalanceOperationAmount


class CreateRequest(Base):
    ticker: instrument_schemas.Ticker


class Create(Base):
    instrument_id: UUID
    operation_type: models.balance_operation.OperationType


class Update(BaseModel):
    pass


class Read(Base):
    operation_type: models.balance_operation.OperationType
    model_config = ConfigDict(from_attributes=True)


class OperationSuccess(BaseModel):
    success: bool = True


class Filters(core.schemas.BaseFilters):
    user_id: UUID | None = None
    ticker: instrument_schemas.Ticker | None = None
    amount_from: BalanceOperationAmount | None = None
    amount_to: BalanceOperationAmount | None = None
    operation_type: models.balance_operation.OperationType | None = None


class SortFields(enum.StrEnum):
    USER_ID = "user_id"
    TICKER = "ticker"
    AMOUNT = "amount"
    OPERATION_TYPE = "operation_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class BalanceOperationReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
