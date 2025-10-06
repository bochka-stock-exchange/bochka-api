import pytest
from fastapi import status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_users_success(client: AsyncClient):
    user_data = {"name": "Test User"}
    response = await client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["name"] == "Test User"
    assert json_response["role"] == "USER"
    assert json_response.get("api_key", None) is not None

    user_data = {"name": "Test User2"}
    response = await client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["name"] == "Test User2"
    assert json_response["role"] == "USER"
    assert json_response.get("api_key", None) is not None


async def test_register_user_invalid_data(client: AsyncClient):
    user_data = {"name": "ab"}
    response = await client.post("/public/register", json=user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
