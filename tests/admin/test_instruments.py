import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import Instrument, User

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_instrument_success(
    db_session: AsyncSession,
    client: AsyncClient,
    admin_user: User,
):
    instrument_data = {"ticker": "USD", "name": "Доллар США"}
    headers = {"Authorization": f"TOKEN {admin_user.api_key}"}
    response = await client.post("/admin/instrument", json=instrument_data, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response["name"] == "Доллар США"
    assert json_response["ticker"] == "USD"

    await db_session.flush()

    result = await db_session.scalars(select(Instrument))

    res = result.all()
    assert len(res) == 1
    instr = res[0]
    assert isinstance(instr, Instrument)
    assert instr.ticker == "USD"
