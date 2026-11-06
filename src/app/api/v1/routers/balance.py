from uuid import UUID

from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies
from src.core.schemas import PaginationParams
from src.core.utils.decorators import retry_on_serialization

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get(
    "",
    response_model=schemas.balance.Response,
)
@retry_on_serialization()
async def get_balance(
    uow: dependencies.uow.Postgres,
    current_user: dependencies.permissions.CurrentUser,
    balances_service: dependencies.services.Balances,
    instruments_service: dependencies.services.Instruments,
):
    all_instruments = await instruments_service.get_all_instruments(uow)

    user_balances = await balances_service.read_many(
        uow,
        filters=schemas.balance.Filters(user_id=current_user.id),
        pagination=PaginationParams(limit=0),
    )

    user_balances_dict = {balance.instrument_id: balance.amount for balance in user_balances}

    return {
        instrument.ticker: user_balances_dict.get(instrument.id, 0)
        for instrument in all_instruments
    }


@router.get(
    "/{ticker}",
    response_model=schemas.balance.Read,
)
async def get_or_create_user_balance(
    uow: dependencies.uow.Postgres,
    ticker: schemas.instruments.Ticker,
    instruments_service: dependencies.services.Instruments,
    balances_service: dependencies.services.Balances,
    user_id: UUID,
):
    instrument = await instruments_service.read_by_ticker(uow, ticker)

    return await balances_service.get_or_create_user_balance(
        uow,
        user_id=user_id,
        instrument_id=instrument.id,
    )
