import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_users_success(anonim_client: AsyncClient):
    user_data = {"name": "Test User"}
    response = await anonim_client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["name"] == "Test User"
    assert json_response["role"] == "USER"
    assert json_response["api_key"].startswith("key-")

    user_data = {"name": "Test User2"}
    response = await anonim_client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["name"] == "Test User2"
    assert json_response["role"] == "USER"
    assert json_response["api_key"].startswith("key-")


async def test_transaction_rollback_check(db_session: AsyncSession):
    res = await db_session.scalars(select(User))
    users = res.all()
    assert len(users) == 0

    user = User(name="Test User", role=UserRole.USER, api_key="test-key")
    db_session.add(user)
    await db_session.flush()

    res = await db_session.scalars(select(User))
    users = res.all()
    assert len(users) == 1
    assert users[0].name == "Test User"


async def test_register_user_invalid_data(anonim_client: AsyncClient):
    user_data = {"name": "ab"}
    response = await anonim_client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
