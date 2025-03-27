import pytest

from src.core import utils

pytestmark = pytest.mark.asyncio(loop_scope="session")


def test_singleton():
    @utils.Singleton
    class Decorated:
        def __init__(self, value):
            self.value = value

    first = Decorated("first")
    second = Decorated("second")

    assert first is second
    assert second.value == "first"
