from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.permissions.get_admin_user)],
    response_model=schemas.instruments.Read,
)
async def create_instrument(
    instrument: schemas.instruments.Create,
    instruments_service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return await instruments_service.create(uow, instrument)


@router.delete(
    "/instrument/{ticker}", dependencies=[Depends(dependencies.permissions.get_admin_user)]
)
async def delete_instrument(
    ticker: str,
    service: dependencies.services.Instruments,
    uow: dependencies.uow.Postgres,
):
    return {"success": await service.delete_by_id(uow, ticker)}


@router.delete("/user/{user_id}", dependencies=[Depends(dependencies.permissions.get_admin_user)])
async def delete_user(
    user_id: UUID,
    service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
):
    return {"success": await service.delete_by_id(uow, user_id)}


@router.post("/balance/deposit", dependencies=[Depends(dependencies.permissions.get_admin_user)])
async def deposit_balance(
    service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
):
    raise NotImplementedError


@router.post("/balance/withdraw", dependencies=[Depends(dependencies.permissions.get_admin_user)])
async def withdraw_balance(
    service: dependencies.services.Users,
    uow: dependencies.uow.Postgres,
):
    raise NotImplementedError
