import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


def test_ping():
    assert True
