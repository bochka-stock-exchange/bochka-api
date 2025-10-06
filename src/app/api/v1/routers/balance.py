from fastapi import APIRouter

from src.app import schemas
from src.app.api import dependencies
from src.core.schemas import PaginationParams

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get(
    "",
    response_model=schemas.balance.Response,
)
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
        pagination=PaginationParams(limit=1000),
    )

    user_balances_dict = {balance.instrument_id: balance.amount for balance in user_balances}

    return {
        instrument.ticker: user_balances_dict.get(instrument.id, 0)
        for instrument in all_instruments
    }
