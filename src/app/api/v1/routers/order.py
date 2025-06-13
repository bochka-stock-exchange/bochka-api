from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import models, schemas
from src.app.api import dependencies

router = APIRouter(prefix="/order", tags=["order"])


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=schemas.orders.CreateSuccess,
)
async def create_order(
    order_data: schemas.orders.Create,
    orders_service: dependencies.services.Orders,
    current_user: dependencies.permissions.CurrentUser,
    uow: dependencies.uow.Postgres,
):
    order = await orders_service.create(
        uow,
        order_data,
        additional_data={
            "user_id": current_user.id,
            "order_type": "LIMIT" if order_data.price else "MARKET",
        },
    )
    return schemas.orders.CreateSuccess(order_id=order.id)


@router.get("", response_model=list[schemas.orders.LimitOrder | schemas.orders.MarketOrder])
async def get_my_orders(
    orders_service: dependencies.services.Orders,
    uow: dependencies.uow.Postgres,
    current_user: dependencies.permissions.CurrentUser,
):
    return [
        schemas.orders.LimitOrder.model_validate(order)
        if order.price
        else schemas.orders.MarketOrder.model_validate(order)
        for order in await orders_service.read_many(
            uow, filters=schemas.orders.Filters(user_id=current_user.id)
        )
    ]


@router.get(
    "/{order_id}",
    dependencies=[Depends(dependencies.permissions.get_current_user)],
    response_model=schemas.orders.LimitOrder | schemas.orders.MarketOrder,
)
async def get_order(
    order_id: UUID, orders_service: dependencies.services.Orders, uow: dependencies.uow.Postgres
):
    order = await orders_service.read_by_id(uow, order_id)
    return (
        schemas.orders.LimitOrder.model_validate(order)
        if order.price
        else schemas.orders.MarketOrder.model_validate(order)
    )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.orders.SuccessResponse,
)
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

    await orders_service.cancel_order(uow, order_id)

    return schemas.orders.SuccessResponse()
