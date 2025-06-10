import random
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src import core
from src.app import schemas, services
from src.app.api import dependencies
from src.core.utils.decorators import retry_on_serialization

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.instruments.CreateResponse,
)
@retry_on_serialization()
async def create_instrument(
    instrument: schemas.instruments.Create,
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return schemas.instruments.CreateResponse(
        success=bool(await instruments_service.create(uow, instrument)),
    )


@router.delete(
    "/instrument/{ticker}",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.instruments.Delete,
)
@retry_on_serialization()
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
@retry_on_serialization()
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
@retry_on_serialization()
async def deposit(
    uow: dependencies.uow.Postgres,
    balance_operation: schemas.balance.CreateRequest,
    balance_service: dependencies.services.Balances,
    user_service: dependencies.services.Users,
    instrument_service: dependencies.services.Instruments,
):
    await user_service.read_by_id(uow, balance_operation.user_id)
    instrument = await instrument_service.read_by_ticker(uow, balance_operation.ticker)

    try:
        balance = await balance_service.read_by_id(
            uow,
            {"user_id": balance_operation.user_id, "instrument_id": instrument.id},
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

    return schemas.balance.OperationSuccess(success=True)


@router.post(
    "/balance/withdraw",
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.balance.OperationSuccess,
)
@retry_on_serialization()
async def withdraw(
    uow: dependencies.uow.Postgres,
    balance_operation: schemas.balance.CreateRequest,
    balance_service: dependencies.services.Balances,
    user_service: dependencies.services.Users,
    instrument_service: dependencies.services.Instruments,
):
    await user_service.read_by_id(uow, balance_operation.user_id)
    instrument = await instrument_service.read_by_ticker(uow, balance_operation.ticker)

    try:
        balance = await balance_service.read_by_id(
            uow,
            {"user_id": balance_operation.user_id, "instrument_id": instrument.id},
        )

        if balance.amount < balance_operation.amount:
            raise services.exceptions.InsufficientBalanceError(
                balance_operation.user_id,
                instrument.ticker,
            )

        await balance_service.update_by_id(
            uow,
            {"user_id": balance_operation.user_id, "instrument_id": instrument.id},
            schemas.balance.Update(amount=balance.amount - balance_operation.amount),
        )
    except core.services.exceptions.EntityNotFoundError:
        raise services.exceptions.InsufficientBalanceError(
            balance_operation.user_id,
            instrument.ticker,
        ) from None

    return schemas.balance.OperationSuccess(success=True)
