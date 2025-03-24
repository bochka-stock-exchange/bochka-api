from fastapi import APIRouter, Depends, HTTPException, status

import src.services.exceptions as service_exceptions
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
    """
    Creates a new instrument and returns its details.
    
    This function uses the provided instrument creation payload to create a new
    instrument via the service layer. If the creation process encounters an error,
    an HTTPException with a 400 status code is raised.
    
    Args:
        instrument: Data required for creating the instrument.
    
    Returns:
        The details of the newly created instrument.
    
    Raises:
        HTTPException: If instrument creation fails.
    """
    try:
        new_instrument = await service.create(session, instrument)
        return new_instrument
    except service_exceptions.EntityCreateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/instrument/{ticker}", dependencies=[Depends(get_admin_user)])
async def delete_instrument(
    ticker: str,
    service: InstrumentServiceDependency,
    session: SessionDependency,
):
    """
    Delete an instrument by its ticker.
    
    Removes an instrument identified by its ticker from the system. Returns a success
    response upon deletion, and raises an HTTPException with a 400 status code for a deletion
    error or a 404 status code if the instrument is not found.
    
    Args:
        ticker: The ticker identifier of the instrument to delete.
    
    Returns:
        A dictionary with a key 'success' set to True if the deletion is successful.
    
    Raises:
        HTTPException: If deletion fails due to an error or if the instrument is missing.
    """
    try:
        await service.delete_by_id(session, ticker)

        return {"success": True}
    except service_exceptions.EntityDeleteError as de:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(de)) from de
    except service_exceptions.EntityNotFoundError as nfe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(nfe)) from nfe
