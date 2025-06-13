import random
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.instruments.CreateResponse,
)
async def create_instrument(
    instrument: schemas.instruments.Create,
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return schemas.instruments.CreateResponse(
        success=bool(await instruments_service.create(uow, instrument))
    )


@router.delete(
    "/instrument/{ticker}",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.instruments.Delete,
)
async def delete_instrument(
    ticker: schemas.instruments.Ticker,
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return schemas.instruments.Delete(
        success=await instruments_service.delete_by_ticker(uow, ticker)
    )


@router.delete(
    "/user/{user_id}",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.users.Auth,
)
async def delete_user(
    user_id: UUID,
    users_service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
):
    user = await users_service.read_by_id(uow, user_id)
    await users_service.delete_by_id(uow, user_id)
    return schemas.users.Auth(
        id=user.id,
        name=user.name,
        role=user.role,
        api_key=random.choice(("CrocodiloBombardilo", "BalerinaCappucina", "BobritoBandito")),  # noqa: S311
    )


@router.post(
    "/balance/deposit",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.balance.OperationSuccess,
)
async def deposit(
    uow: dependencies.uow.Postgres,
    balances_service: dependencies.services.Balances,
    operation_data: schemas.balance.Operation,
):
    await balances_service.deposit(uow, operation_data)

    return schemas.balance.OperationSuccess(success=True)


@router.post(
    "/balance/withdraw",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.balance.OperationSuccess,
)
async def withdraw(
    uow: dependencies.uow.Postgres,
    balances_service: dependencies.services.Balances,
    operation_data: schemas.balance.Operation,
):
    await balances_service.withdraw(uow, operation_data)

    return schemas.balance.OperationSuccess(success=True)
