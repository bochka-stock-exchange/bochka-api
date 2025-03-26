import pytest

import src.utils as utils

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_singleton():
    @utils.SingletonDecorator
    class Decorated:
        def __init__(self, value):
            self.value = value

    first = Decorated("first")
    second = Decorated("second")

    assert first is second
    assert second.value == "first"
