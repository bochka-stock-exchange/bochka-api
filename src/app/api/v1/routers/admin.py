from fastapi import APIRouter, Depends, status

from src.app import schemas
from src.app.api import dependencies

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_admin_user)],
    response_model=schemas.instruments.Read,
)
async def create_instrument(
    instrument: schemas.instruments.Create,
    instruments_service: dependencies.InstrumentsService,
    uow: dependencies.UoWPostgres,
):
    return await instruments_service.create(uow, instrument)


@router.delete("/instrument/{ticker}", dependencies=[Depends(dependencies.get_admin_user)])
async def delete_instrument(
    ticker: str,
    instruments_service: dependencies.InstrumentsService,
    uow: dependencies.UoWPostgres,
):
    await instruments_service.delete_by_id(uow, ticker)
    return {"deleted": ticker}
