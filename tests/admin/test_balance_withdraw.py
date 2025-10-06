from collections.abc import Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_withdraw_success(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    balance: models.Balance,
):
    initial_amount = balance.amount

    withdraw_amount = 500
    withdraw_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": withdraw_amount,
    }

    response = await admin_client.post("/admin/balance/withdraw", json=withdraw_data)

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["success"]

    assert balance.amount == initial_amount - withdraw_amount

    operation = await db_session.scalar(
        select(models.BalanceOperation).filter_by(
            user_id=admin_user.id, instrument_id=instrument.id, amount=withdraw_amount
        )
    )

    assert operation is not None
    assert operation.operation_type == "WITHDRAW"


async def test_withdraw_failed_not_enough_funds(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    balance: models.Balance,
):
    initial_amount = balance.amount

    withdraw_amount = initial_amount + 100
    withdraw_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": withdraw_amount,
    }

    response = await admin_client.post("/admin/balance/withdraw", json=withdraw_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error_code") == "not_enough_funds"


async def test_withdraw_failed_no_balance(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
):
    withdraw_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": 100,
    }

    response = await admin_client.post("/admin/balance/withdraw", json=withdraw_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error_code") == "not_enough_funds"


async def test_withdraw_failed_user_not_found(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    instrument: models.Instrument,
):
    withdraw_data = {
        "user_id": str(uuid7()),
        "ticker": instrument.ticker,
        "amount": 100,
    }

    response = await admin_client.post("/admin/balance/withdraw", json=withdraw_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error_code") == "resource_not_found"


async def test_withdraw_failed_instrument_not_found(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
):
    withdraw_data = {
        "user_id": str(admin_user.id),
        "ticker": "NONEXIST",
        "amount": 100,
    }

    response = await admin_client.post("/admin/balance/withdraw", json=withdraw_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error_code") == "resource_not_found"


@pytest.mark.parametrize(
    "withdraw_data",
    [
        # Negative amount
        lambda user, instrument: {
            "user_id": str(user.id),
            "ticker": instrument.ticker,
            "amount": -100,
        },
        # Zero amount
        lambda user, instrument: {
            "user_id": str(user.id),
            "ticker": instrument.ticker,
            "amount": 0,
        },
        # Invalid user_id type (int)
        lambda user, instrument: {  # noqa: ARG005
            "user_id": 12345,
            "ticker": instrument.ticker,
            "amount": 100,
        },
        # Invalid user_id format (not a uuid)
        lambda user, instrument: {  # noqa: ARG005
            "user_id": "not-a-uuid",
            "ticker": instrument.ticker,
            "amount": 100,
        },
        # Invalid amount type (string)
        lambda user, instrument: {
            "user_id": str(user.id),
            "ticker": instrument.ticker,
            "amount": "ABC",
        },
        # Invalid amount type (float)
        lambda user, instrument: {
            "user_id": str(user.id),
            "ticker": instrument.ticker,
            "amount": 100.50,
        },
        # Missing user_id
        lambda user, instrument: {"ticker": instrument.ticker, "amount": 100},  # noqa: ARG005
        # Missing ticker
        lambda user, instrument: {"user_id": str(user.id), "amount": 100},  # noqa: ARG005
        # Missing amount
        lambda user, instrument: {
            "user_id": str(user.id),
            "ticker": instrument.ticker,
        },
    ],
)
async def test_withdraw_failed_validation(
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    withdraw_data: Callable,
):
    data = withdraw_data(admin_user, instrument)
    response = await admin_client.post("/admin/balance/withdraw", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
