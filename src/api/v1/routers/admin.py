from fastapi import APIRouter, Depends, HTTPException, status

import src.api.v1.dependencies as dependencies
import src.services.exceptions as service_exceptions
from src.schemas.instrument import InstrumentCreate, InstrumentRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_admin_user)],
    response_model=InstrumentRead,
)
async def create_instrument(
    instrument: InstrumentCreate,
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.Session,
):
    try:
        new_instrument = await instruments_service.create(session, instrument)
        return new_instrument
    except service_exceptions.EntityCreateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/instrument/{ticker}", dependencies=[Depends(dependencies.get_admin_user)])
async def delete_instrument(
    ticker: str,
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.Session,
):
    try:
        await instruments_service.delete_by_id(session, ticker)

        return {"success": True}
    except service_exceptions.EntityDeleteError as de:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(de)) from de
    except service_exceptions.EntityNotFoundError as nfe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(nfe)) from nfe
