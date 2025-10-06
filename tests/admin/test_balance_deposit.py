from collections.abc import Callable

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

from src.app import models

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_deposit_success_new_balance(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
):
    amount_test = 1000
    deposit_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": amount_test,
    }

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    json_response = response.json()
    assert "detail" not in json_response
    assert json_response["success"]

    # Check balance was created
    balance = await db_session.scalar(
        select(models.Balance).filter_by(user_id=admin_user.id, instrument_id=instrument.id)
    )
    assert balance is not None
    assert balance.amount == amount_test

    # Check operation was created
    operation = await db_session.scalar(
        select(models.BalanceOperation).filter_by(
            user_id=admin_user.id,
            instrument_id=instrument.id,
        )
    )
    assert operation is not None
    assert operation.amount == amount_test
    assert operation.operation_type == models.balance_operation.OperationType.DEPOSIT


async def test_deposit_success_existing_balance(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    balance: models.Balance,
):
    initial_amount = balance.amount
    deposit_amount = 500

    deposit_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": deposit_amount,
    }

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    json_response = response.json()
    assert "detail" not in json_response
    assert json_response["success"]

    assert balance.amount == initial_amount + deposit_amount

    # Check operation was created
    operation = await db_session.scalar(
        select(models.BalanceOperation).filter_by(
            user_id=admin_user.id,
            instrument_id=instrument.id,
            amount=deposit_amount,
        )
    )
    assert operation is not None


async def test_deposit_failed_user_not_found(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    instrument: models.Instrument,
):
    deposit_data = {
        "user_id": str(uuid7()),
        "ticker": instrument.ticker,
        "amount": 1000,
    }

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error_code") == "resource_not_found"


async def test_deposit_failed_instrument_not_found(
    db_session: AsyncSession,
    admin_client: AsyncClient,
    admin_user: models.User,
):
    deposit_data = {"user_id": str(admin_user.id), "ticker": "NONEXIST", "amount": 1000}

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("error_code") == "resource_not_found"


@pytest.mark.parametrize(
    "deposit_data",
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
        lambda user, instrument: {"user_id": 12345, "ticker": instrument.ticker, "amount": 1000},  # noqa: ARG005
        # Invalid user_id format (not a uuid)
        lambda user, instrument: {  # noqa: ARG005
            "user_id": "not-a-uuid",
            "ticker": instrument.ticker,
            "amount": 1000,
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
            "amount": 1000.50,
        },
        # Missing user_id
        lambda user, instrument: {"ticker": instrument.ticker, "amount": 1000},  # noqa: ARG005
        # Missing ticker
        lambda user, instrument: {"user_id": str(user.id), "amount": 1000},  # noqa: ARG005
        # Missing amount
        lambda user, instrument: {"user_id": str(user.id), "ticker": instrument.ticker},
    ],
)
async def test_deposit_failed_validation(
    admin_client: AsyncClient,
    admin_user: models.User,
    instrument: models.Instrument,
    deposit_data: Callable,
):
    data = deposit_data(admin_user, instrument)

    response = await admin_client.post("/admin/balance/deposit", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_admin_can_deposit_to_user(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    user: models.User,
    instrument: models.Instrument,
):
    amount_test = 1000
    deposit_data = {"user_id": str(user.id), "ticker": instrument.ticker, "amount": amount_test}

    response = await admin_client.post("/admin/balance/deposit", json=deposit_data)

    json_response = response.json()
    assert "detail" not in json_response
    assert json_response["success"]

    balance = await db_session.scalar(
        select(models.Balance).filter_by(user_id=user.id, instrument_id=instrument.id)
    )
    assert balance is not None
    assert balance.amount == amount_test

    operation = await db_session.scalar(
        select(models.BalanceOperation).filter_by(
            user_id=user.id,
            instrument_id=instrument.id,
        )
    )
    assert operation is not None
    assert operation.amount == amount_test
    assert operation.operation_type == models.balance_operation.OperationType.DEPOSIT


async def test_user_cannot_deposit_to_admin(
    user_client: AsyncClient,
    db_session: AsyncSession,
    admin_user: models.User,
    instrument: models.Instrument,
):
    amount_test = 1000
    deposit_data = {
        "user_id": str(admin_user.id),
        "ticker": instrument.ticker,
        "amount": amount_test,
    }

    response = await user_client.post("/admin/balance/deposit", json=deposit_data)

    json_response = response.json()
    assert "detail" in json_response
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert json_response.get("error_code") == "forbidden_access"
