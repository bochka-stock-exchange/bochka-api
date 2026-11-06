import pytest
from httpx import AsyncClient

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_one_balance(
    admin_client: AsyncClient,
    instrument: models.Instrument,
    admin_balance: models.Balance,
):
    response = await admin_client.get("/balance")

    json_response = response.json()
    assert "detail" not in json_response
    assert len(json_response) == 1
    assert json_response.get(instrument.ticker) == admin_balance.amount


async def test_no_balances(user_client: AsyncClient):
    response = await user_client.get("/balance")

    assert response.json() == {}


async def test_two_balances(
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    admin_balance: models.Balance,
):
    instrument_data = {"ticker": "USD", "name": "Доллар США"}
    response = await admin_client.post("/admin/instrument", json=instrument_data)

    assert "detail" not in response.json()

    amount_test = 1000
    deposit_data = {
        "user_id": str(admin_user.id),
        "ticker": "USD",
        "amount": amount_test,
    }

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    assert "detail" not in response.json()

    response = await admin_client.get("/balance")

    json_response = response.json()
    assert "detail" not in json_response
    assert len(json_response) == 2  # noqa: PLR2004
    assert json_response.get(instrument.ticker) == admin_balance.amount
    assert json_response.get("USD") == amount_test


async def test_two_balances_one_empty(
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    admin_balance: models.Balance,
):
    instrument_data = {"ticker": "USD", "name": "Доллар США"}
    response = await admin_client.post("/admin/instrument", json=instrument_data)

    assert "detail" not in response.json()

    response = await admin_client.get("/balance")

    json_response = response.json()
    assert "detail" not in json_response
    assert len(json_response) == 2  # noqa: PLR2004
    assert json_response.get(instrument.ticker) == admin_balance.amount
    assert json_response.get("USD") == 0
