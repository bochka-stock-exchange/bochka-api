from src.core import utils


def test_singleton():
    @utils.decorators.Singleton
    class Decorated:
        def __init__(self, value):
            self.value = value

    first = Decorated("first")
    second = Decorated("second")

    assert first is second
    assert second.value == "first"
