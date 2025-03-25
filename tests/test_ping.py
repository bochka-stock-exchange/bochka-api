import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_ping():
    assert True
