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
    instrument_service: dependencies.services.Instruments,
    current_user: dependencies.permissions.CurrentUser,
    uow: dependencies.uow.Postgres,
):
    instrument = await instrument_service.read_by_ticker(uow, order_data.ticker)

    order = await orders_service.create(
        uow,
        order_data,
        additional_data={
            "instrument_id": instrument.id,
            "user_id": current_user.id,
            "status": "NEW" if hasattr(order_data, "price") else "EXECUTED",
            "order_type": "LIMIT" if hasattr(order_data, "price") else "MARKET",
        },
    )
    return schemas.orders.CreateSuccess(order_id=order.id)


@router.get("", dependencies=[Depends(dependencies.permissions.get_current_user)])
async def get_my_orders():
    raise NotImplementedError


@router.get(
    "/{order_id}",
    dependencies=[Depends(dependencies.permissions.get_current_user)],
    response_model=schemas.orders.Read,
)
async def get_order(
    order_id: UUID, order_service: dependencies.services.Orders, uow: dependencies.uow.Postgres
):
    return await order_service.read_by_id(uow, order_id)


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
            message="You dont have permission to cancel this order", service_name="Orders"
        )

    await orders_service.update_by_id(
        uow, order_id, schemas.orders.Update(status=models.order.OrderStatus.CANCELLED)
    )

    # Since cancelled orders should not be released with all of them and cannot be restored,
    # we delete them so as not to make additional status checks.
    await orders_service.delete_by_id(uow, order_id)

    return schemas.orders.SuccessResponse()
