import enum
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)

from src import core
from src.app import models

from . import instruments as instrument_schemas

settings = core.config.get_settings()

LimitOrderPrice = Annotated[int, Field(gt=0)]
OrderQuantity = Annotated[int, Field(ge=1)]


class Base(BaseModel):
    direction: models.order.Direction
    ticker: instrument_schemas.Ticker
    qty: OrderQuantity


class Create(Base):
    price: LimitOrderPrice | None = None


class LimitOrderBody(Base):
    price: LimitOrderPrice


class MarketOrderBody(Base):
    pass


class Read(BaseModel):
    id: UUID
    status: models.order.OrderStatus
    user_id: UUID
    created_at: Annotated[datetime, Field(serialization_alias="timestamp")]

    instrument: Annotated[instrument_schemas.Read, Field(exclude=True)]
    direction: Annotated[models.order.Direction, Field(exclude=True)]
    qty: Annotated[OrderQuantity, Field(exclude=True)]
    price: Annotated[LimitOrderPrice | None, Field(exclude=True)]

    filled: int | None

    @computed_field
    @property
    def body(self) -> LimitOrderBody | MarketOrderBody:
        return (
            LimitOrderBody(
                direction=self.direction,
                ticker=self.instrument.ticker,
                qty=self.qty,
                price=self.price,
            )
            if self.price
            else MarketOrderBody(
                direction=self.direction, ticker=self.instrument.ticker, qty=self.qty
            )
        )

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Update(BaseModel):
    status: models.order.OrderStatus | None = None


class SuccessResponse(BaseModel):
    success: bool = True


class CreateSuccess(SuccessResponse):
    order_id: UUID


class Filters(core.schemas.BaseFilters):
    direction: list[models.order.Direction] | models.order.Direction | None = None
    ticker: list[instrument_schemas.Ticker] | instrument_schemas.Ticker | None = None
    status: list[models.order.OrderStatus] | models.order.OrderStatus | None = None
    user_id: list[UUID] | UUID | None = None
    price_from: LimitOrderPrice | None = None
    price_to: LimitOrderPrice | None = None


class SortFields(enum.StrEnum):
    DIRECTION = "direction"
    QUANTITY = "qty"
    PRICE = "price"
    STATUS = "status"
    TICKER = "ticker"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortParams(core.schemas.SortParams):
    sort_by: SortFields | None = None


class ReadManyParams(Filters, SortParams, core.schemas.PaginationParams):
    pass
