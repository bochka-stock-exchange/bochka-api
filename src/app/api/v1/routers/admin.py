import random
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import models, schemas
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
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return schemas.instruments.Delete(success=await service.delete_by_ticker(uow, ticker))


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
    response_model=schemas.balance_operations.OperationSuccess,
)
async def deposit(
    uow: dependencies.uow.Postgres,
    balance_operation: schemas.balance_operations.CreateRequest,
    balance_service: dependencies.services.Balances,
    balance_operation_service: dependencies.services.BalanceOperations,
    user_service: dependencies.services.Users,
    instrument_service: dependencies.services.Instruments,
):
    await user_service.read_by_id(uow, balance_operation.user_id)
    instrument = await instrument_service.read_by_ticker(uow, balance_operation.ticker)

    try:
        balance = await balance_service.read_by_id(
            uow, {"user_id": balance_operation.user_id, "instrument_id": instrument.id}
        )

        await balance_service.update_by_id(
            uow,
            {"user_id": balance_operation.user_id, "instrument_id": instrument.id},
            schemas.balance.Update(amount=balance.amount + balance_operation.amount),
        )
    except core.services.exceptions.EntityNotFoundError:
        await balance_service.create(
            uow,
            schemas.balance.Create(
                user_id=balance_operation.user_id,
                amount=balance_operation.amount,
                instrument_id=instrument.id,
            ),
        )

    await balance_operation_service.create(
        uow,
        schemas.balance_operations.Create(
            user_id=balance_operation.user_id,
            amount=balance_operation.amount,
            instrument_id=instrument.id,
            operation_type=models.balance_operation.OperationType.DEPOSIT,
        ),
    )

    return schemas.balance_operations.OperationSuccess(success=True)


@router.post(
    "/balance/withdraw",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.balance_operations.OperationSuccess,
)
async def withdraw(
    uow: dependencies.uow.Postgres,
    balance_operation: schemas.balance_operations.CreateRequest,
    balance_service: dependencies.services.Balances,
    operation_service: dependencies.services.BalanceOperations,
    user_service: dependencies.services.Users,
    instrument_service: dependencies.services.Instruments,
):
    await user_service.read_by_id(uow, balance_operation.user_id)
    instrument = await instrument_service.read_by_ticker(uow, balance_operation.ticker)

    try:
        balance = await balance_service.read_by_id(
            uow, {"user_id": balance_operation.user_id, "instrument_id": instrument.id}
        )

        if balance.amount < balance_operation.amount:
            raise dependencies.exceptions.NotEnoughFundsError(
                balance_operation.user_id, instrument.ticker
            )

        await balance_service.update_by_id(
            uow,
            {"user_id": balance_operation.user_id, "instrument_id": instrument.id},
            schemas.balance.Update(amount=balance.amount - balance_operation.amount),
        )
    except core.services.exceptions.EntityNotFoundError:
        raise dependencies.exceptions.NotEnoughFundsError(
            balance_operation.user_id, instrument.ticker
        ) from None

    await operation_service.create(
        uow,
        schemas.balance_operations.Create(
            user_id=balance_operation.user_id,
            amount=balance_operation.amount,
            instrument_id=instrument.id,
            operation_type=models.balance_operation.OperationType.WITHDRAW,
        ),
    )

    return schemas.balance_operations.OperationSuccess(success=True)
