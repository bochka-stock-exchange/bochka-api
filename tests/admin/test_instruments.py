import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import schemas
from src.app.models import Instrument

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.mark.xfail
async def test_create_instrument_success(
    db_session: AsyncSession,
    client: AsyncClient,
    admin_user: schemas.users.Read,
):
    instrument_data = {"ticker": "USD", "name": "Доллар США"}
    response = await client.post("/admin/instrument", json=instrument_data)

    assert response.status_code == status.HTTP_201_CREATED
    json_response = response.json()
    assert json_response.get("name") == "Доллар США"
    assert json_response.get("ticker") == "USD"

    result = await db_session.scalars(select(Instrument))

    res = result.all()
    assert len(res) == 1
    instr = res[0]
    assert isinstance(instr, Instrument)
    assert instr.ticker == "USD"


async def test_create_instrument_duplicate(
    db_session: AsyncSession,
    admin_client: AsyncClient,
):
    instrument_data = {"ticker": "USD", "name": "Доллар США"}
    response = await admin_client.post("/admin/instrument", json=instrument_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("ticker") == "USD"

    response = await admin_client.post("/admin/instrument", json=instrument_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert response.json().get("error_code") == "create_failed_duplicate"


async def test_delete_instrument_failed_404(
    db_session: AsyncSession,
    admin_client: AsyncClient,
):
    ticker = "FAKE"

    response = await admin_client.delete(f"/admin/instrument/{ticker}")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json().get("error_code") == "resource_not_found"


@pytest.mark.xfail
async def test_delete_instrument_failed_401(
    db_session: AsyncSession,
    client: AsyncClient,
):
    ticker = "FAKE"

    response = await client.delete(f"/admin/instrument/{ticker}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    assert response.json().get("error_code") == "authentication_failed"


async def test_delete_instrument_failed_403(
    db_session: AsyncSession,
    user_client: AsyncClient,
):
    ticker = "FAKE"

    response = await user_client.delete(f"/admin/instrument/{ticker}")

    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert response.json().get("error_code") == "forbidden_access"
