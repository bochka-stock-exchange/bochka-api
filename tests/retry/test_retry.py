from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import models, repositories
from src.core.uow import UnitOfWork

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_serialization_error() -> OperationalError:
    class CustomError(Exception):
        def __init__(self, pgcode: str):
            super().__init__()
            self.pgcode = pgcode

    orig = CustomError("40001")
    return OperationalError("serialization error", params=None, orig=orig)


@pytest.mark.slow
async def test_create_retries_on_serialization_error(mock_uow: None, db_session: AsyncSession):
    instruments_repo = repositories.Instruments()

    retries_number = 3

    flush_count = 0
    original_flush = db_session.flush

    async def mocked_flush(*args, **kwargs):
        nonlocal flush_count
        flush_count += 1

        if flush_count < retries_number:
            raise make_serialization_error()

        return await original_flush(*args, **kwargs)

    refresh_mock = (
        AsyncMock()
    )  # Fix to "Instance '<Instrument at 0x1f301df9550>' is not persistent within this Session"

    async with UnitOfWork(use_postgres=False) as uow:
        with (
            patch.object(uow.postgres_session, "flush", mocked_flush),
            patch.object(uow.postgres_session, "refresh", refresh_mock),
        ):
            result = await instruments_repo.create(
                uow,
                {"ticker": "TESTTEST", "name": "Test Instrument"},
            )

    results = (await db_session.scalars(select(models.Instrument))).all()

    assert len(results) == 1
    assert getattr(results[0], "ticker", None) == "TESTTEST"

    assert flush_count == retries_number

    refresh_mock.assert_awaited_once_with(result)


async def test_isolation_level_serializable(db_session: AsyncSession):
    isolation = await db_session.scalar(text("SHOW transaction_isolation"))
    assert isolation == "serializable"


@pytest.mark.slow
async def test_endpoint_retries_on_serialization_error(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    retries_number = 4

    flush_count = 0
    original_flush = db_session.flush

    async def mocked_flush(*args, **kwargs):
        nonlocal flush_count
        flush_count += 1

        if flush_count < retries_number:
            raise make_serialization_error()

        return await original_flush(*args, **kwargs)

    monkeypatch.setattr(db_session, "flush", mocked_flush)

    response = await admin_client.post(
        "/admin/instrument",
        json={"ticker": "RETRY", "name": "Retry Test"},
    )

    assert "detail" not in response.json()
    assert response.json()["success"]

    assert flush_count == retries_number

    instruments = (await db_session.scalars(select(models.Instrument))).all()

    assert len(instruments) == 1
    assert instruments[0].ticker == "RETRY"
