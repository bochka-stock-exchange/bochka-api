from fastapi import APIRouter, Depends, status

from src.app import schemas
from src.app.api.v1 import dependencies

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
    return await instruments_service.create(session, instrument)


@router.delete("/instrument/{ticker}", dependencies=[Depends(dependencies.get_admin_user)])
async def delete_instrument(
    ticker: str,
    instruments_service: dependencies.InstrumentsService,
    session: dependencies.DBSession,
):
    await instruments_service.delete_by_id(session, ticker)
    return {"deleted": ticker}


@router.get("/users-all", dependencies=[Depends(dependencies.get_admin_user)])
async def get_all_users(
    users_service: dependencies.UsersService,
    session: dependencies.DBSession,
    page: int = 1,
    limit: int = 10,
) -> list[schemas.UserRead]:
    return await users_service.read_all(session, page=page, limit=limit)
