from fastapi import APIRouter, Depends, HTTPException, status

import src.app.api.v1.dependencies as dependencies
import src.app.schemas as schemas
import src.core as core

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dependencies.get_admin_user)],
    response_model=schemas.InstrumentRead,
)
async def create_instrument(
    instrument: schemas.InstrumentCreate,
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.DBSession,
):
    try:
        new_instrument = await instruments_service.create(session, instrument)
        return new_instrument
    except core.services.exceptions.EntityCreateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/instrument/{ticker}", dependencies=[Depends(dependencies.get_admin_user)])
async def delete_instrument(
    ticker: str,
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.DBSession,
):
    try:
        await instruments_service.delete_by_id(session, ticker)

        return {"success": True}
    except core.services.exceptions.EntityDeleteError as de:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(de)) from de
    except core.services.exceptions.EntityNotFoundError as nfe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(nfe)) from nfe
