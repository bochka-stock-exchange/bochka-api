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
OrderFilled = Annotated[int | None, Field(ge=0)]


class OrderBookPaginationParams(core.schemas.PaginationParams):
    limit: Annotated[int, Field(ge=1, le=25)] = 10


class Base(BaseModel):
    direction: models.order.Direction
    ticker: instrument_schemas.Ticker
    qty: OrderQuantity


class CreateRequest(Base):
    price: LimitOrderPrice | None = None


class Create(BaseModel):
    direction: models.order.Direction
    qty: OrderQuantity
    instrument_id: UUID
    user_id: UUID
    price: LimitOrderPrice | None = None
    status: models.order.OrderStatus
    order_type: models.order.OrderType


class LimitOrderBody(Base):
    price: LimitOrderPrice


class MarketOrderBody(Base):
    pass


class Read(BaseModel):
    id: UUID
    status: models.order.OrderStatus
    user_id: UUID
    filled: OrderFilled
    created_at: Annotated[datetime, Field(serialization_alias="timestamp")]

    instrument: Annotated[instrument_schemas.Read, Field(exclude=True)]
    direction: Annotated[models.order.Direction, Field(exclude=True)]
    qty: Annotated[OrderQuantity, Field(exclude=True)]
    price: Annotated[LimitOrderPrice | None, Field(exclude=True)]
    order_type: Annotated[models.order.OrderType, Field(exclude=True)]
    locked_instrument_amount: Annotated[int | None, Field(exclude=True)]
    locked_money_amount: Annotated[int | None, Field(exclude=True)]

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
                direction=self.direction,
                ticker=self.instrument.ticker,
                qty=self.qty,
            )
        )

    def __lt__(self, other: "Read") -> bool:
        if self.direction != other.direction:
            raise ValueError("Cannot compare orders with different directions")

        assert self.price is not None
        assert other.price is not None

        match self.direction:
            case models.order.Direction.SELL:
                return (self.price, self.created_at) < (other.price, other.created_at)
            case models.order.Direction.BUY:
                return (-self.price, self.created_at) < (-other.price, other.created_at)

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class OrderBookLevel(BaseModel):
    price: LimitOrderPrice
    qty: OrderQuantity


class OrderBookRead(BaseModel):
    bid_levels: list[OrderBookLevel]
    ask_levels: list[OrderBookLevel]

    model_config = ConfigDict(from_attributes=True)


class Update(BaseModel):
    filled: OrderFilled = None
    locked_money_amount: Annotated[int | None, Field(ge=0)] = None
    locked_instrument_amount: Annotated[int | None, Field(ge=0)] = None
    status: models.order.OrderStatus | None = None


class SuccessResponse(BaseModel):
    success: bool = True


class CreateSuccess(SuccessResponse):
    order_id: UUID


class Filters(core.schemas.BaseFilters):
    direction: list[models.order.Direction] | models.order.Direction | None = None
    ticker: list[instrument_schemas.Ticker] | instrument_schemas.Ticker | None = None
    status: list[models.order.OrderStatus] | models.order.OrderStatus | None = None
    order_type: list[models.order.OrderType] | models.order.OrderType | None = None
    instrument_id: list[UUID] | UUID | None = None
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
