import pytest
from httpx import ASGITransport, AsyncClient

from src.app.main import app
from src.app.config import get_settings


pytest_plugins = ["pytest_asyncio"]

settings = get_settings()


@pytest.fixture(scope="session")
async def client():
    """Provide an AsyncClient."""
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://test/api/v1"
    ) as client:
        yield client
