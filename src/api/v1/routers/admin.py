from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.dependencies import (
    InstrumentServiceDependency,
    SessionDependency,
    get_admin_user,
)
from src.schemas.instrument import InstrumentCreate, InstrumentRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/instrument",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
    response_model=InstrumentRead,
)
async def create_instrument(
    instrument: InstrumentCreate,
    service: InstrumentServiceDependency,
    session: SessionDependency,
):
    try:
        new_instrument = await service.create(session, instrument)
        return new_instrument
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/instrument/{ticker}", dependencies=[Depends(get_admin_user)])
async def delete_instrument(
    ticker: str,
    service: InstrumentServiceDependency,
    session: SessionDependency,
):
    try:
        success = await service.delete_by_id(session, ticker)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found",
            )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
