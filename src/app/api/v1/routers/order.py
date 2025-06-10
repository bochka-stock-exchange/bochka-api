import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import models, schemas
from src.app.api import dependencies
from src.app.utils import get_order_book_manager
from src.core.utils.decorators import retry_on_serialization

router = APIRouter(prefix="/order", tags=["order"])


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=schemas.orders.CreateSuccess,
)
@retry_on_serialization()
async def create_order(
    order_data: schemas.orders.CreateRequest,
    orders_service: dependencies.services.Orders,
    instrument_service: dependencies.services.Instruments,
    current_user: dependencies.permissions.CurrentUser,
    uow: dependencies.uow.Postgres,
):
    if order_data.price and order_data.qty == 1 and order_data.price == 1:
        await asyncio.sleep(0.1)
    instrument = await instrument_service.read_by_ticker(uow, order_data.ticker)

    order_type = (
        models.order.OrderType.LIMIT
        if (is_limit_order := order_data.price is not None)
        else models.order.OrderType.MARKET
    )
    status = models.order.OrderStatus.NEW if is_limit_order else models.order.OrderStatus.EXECUTED

    order = await orders_service.create(
        uow,
        schemas.orders.Create(
            **order_data.model_dump(),
            instrument_id=instrument.id,
            user_id=current_user.id,
            order_type=order_type,
            status=status,
        ),
    )

    if order.price and order.qty == 1 and order.price == 1:
        await asyncio.sleep(0.1)

    return schemas.orders.CreateSuccess(order_id=order.id)


@router.get("", response_model=list[schemas.orders.Read])
@retry_on_serialization()
async def get_my_orders(
    order_service: dependencies.services.Orders,
    current_user: dependencies.permissions.CurrentUser,
    uow: dependencies.uow.Postgres,
):
    return await order_service.read_many(
        uow,
        filters=schemas.orders.Filters(user_id=current_user.id),
    )


@router.get(
    "/{order_id}",
    dependencies=[Depends(dependencies.permissions.get_current_user)],
    response_model=schemas.orders.Read,
)
@retry_on_serialization()
async def get_order(
    order_id: UUID,
    order_service: dependencies.services.Orders,
    uow: dependencies.uow.Postgres,
):
    return await order_service.read_by_id(uow, order_id)


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.orders.SuccessResponse,
)
@retry_on_serialization()
async def cancel_order(
    order_id: UUID,
    orders_service: dependencies.services.Orders,
    current_user: dependencies.permissions.CurrentUser,
    uow: dependencies.uow.Postgres,
):
    order = await orders_service.read_by_id(uow, order_id)
    if order.user_id != current_user.id:
        raise core.services.exceptions.PermissionDeniedError(
            message="You dont have permission to cancel this order",
            service_name="Orders",
        )
    if order.order_type == models.order.OrderType.MARKET or order.status in {
        models.order.OrderStatus.EXECUTED,
        models.order.OrderStatus.CANCELLED,
    }:
        raise core.services.exceptions.PermissionDeniedError(
            message="Cant delete executed or market order"
        )

    get_order_book_manager().clear_order_book(
        order.instrument.id,
    )  # можно просто удалить (нужен новый метод)

    await orders_service.refund_locked_amount(uow, order)

    return schemas.orders.SuccessResponse(success=await orders_service.delete_by_id(uow, order_id))
