import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_get_wastes_types():
    assert "test" == "test"
