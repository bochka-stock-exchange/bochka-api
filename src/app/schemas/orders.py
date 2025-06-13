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
from . import users as users_schemas

settings = core.config.get_settings()

LimitOrderPrice = Annotated[int, Field(gt=0)]
OrderQuantity = Annotated[int, Field(ge=1)]


class Base(BaseModel):
    direction: models.order.Direction
    qty: OrderQuantity


class Create(Base):
    ticker: instrument_schemas.Ticker
    price: LimitOrderPrice | None = None


class MarketOrderBody(Base):
    ticker: instrument_schemas.Ticker


class LimitOrderBody(MarketOrderBody):
    price: LimitOrderPrice


class Read(Base):
    id: UUID
    status: models.order.OrderStatus
    order_type: models.order.OrderType
    user_id: UUID
    created_at: Annotated[datetime, Field(serialization_alias="timestamp")]
    instrument_id: UUID

    locked_amount: Annotated[int, Field(ge=0)]

    user: Annotated[users_schemas.Read, Field(exclude=True)]
    instrument: Annotated[instrument_schemas.Read, Field(exclude=True)]
    direction: Annotated[models.order.Direction, Field(exclude=True)]
    qty: Annotated[OrderQuantity, Field(exclude=True)]
    price: Annotated[LimitOrderPrice | None, Field(exclude=True)]

    filled: int

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class MarketOrder(Base):
    id: UUID
    status: models.order.OrderStatus
    user_id: UUID
    created_at: Annotated[datetime, Field(serialization_alias="timestamp")]

    instrument: Annotated[instrument_schemas.Read, Field(exclude=True)]
    direction: Annotated[models.order.Direction, Field(exclude=True)]
    qty: Annotated[OrderQuantity, Field(exclude=True)]

    @computed_field
    @property
    def body(self) -> MarketOrderBody:
        return MarketOrderBody(
            direction=self.direction, ticker=self.instrument.ticker, qty=self.qty
        )

    model_config = ConfigDict(
        from_attributes=True, serialize_by_alias=True, validate_by_alias=True
    )


class LimitOrder(MarketOrder):
    price: Annotated[LimitOrderPrice, Field(exclude=True)]

    @computed_field
    @property
    def body(self) -> LimitOrderBody:
        return LimitOrderBody(
            direction=self.direction,
            ticker=self.instrument.ticker,
            qty=self.qty,
            price=self.price,
        )

    filled: int

    model_config = ConfigDict(
        from_attributes=True, serialize_by_alias=True, validate_by_alias=True
    )


class Update(BaseModel):
    status: models.order.OrderStatus | None = None
    filled: Annotated[int, Field(ge=0)] | None = None
    locked_amount: Annotated[int, Field(ge=0)] | None = None


class SuccessResponse(BaseModel):
    success: bool = True


class CreateSuccess(SuccessResponse):
    order_id: UUID


class OrderBookLevel(BaseModel):
    price: LimitOrderPrice
    qty: OrderQuantity


class OrderBook(BaseModel):
    bid_levels: list[OrderBookLevel]
    ask_levels: list[OrderBookLevel]


class Filters(core.schemas.BaseFilters):
    direction: list[models.order.Direction] | models.order.Direction | None = None
    order_type: list[models.order.OrderType] | models.order.OrderType | None = None
    instrument_id: list[UUID] | UUID | None = None
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
