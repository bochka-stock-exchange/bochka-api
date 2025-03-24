import threading
from typing import TypeVar

from pydantic._internal._model_construction import ModelMetaclass


# ModelMetaclass is harmless for non-pydantic classes
class Singleton(ModelMetaclass):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with cls._lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance

    def __init__(cls, name, bases, attrs):
        super(Singleton, cls).__init__(name, bases, attrs)
        cls._lock = threading.RLock()


T = TypeVar("T")


def SingletonDecorator(cls: type[T]) -> type:
    instance = None
    lock = threading.Lock()
    original_init = cls.__init__

    def get_instance(cls: type[T], *args, **kwargs) -> T:
        nonlocal instance, lock
        if instance is None:
            with lock:
                if instance is None:
                    instance = cls.__new__(cls)
                    original_init(instance, *args, **kwargs)
        return instance

    def __init__(self, *args, **kwargs):
        nonlocal instance
        if instance is not self:
            raise RuntimeError("Use get_instance() to create a singleton instance.")

    """
    X = type('X', (A,B), dict(a=1))
    is equal to
    class X(A,B):
        a=1
    """
    new_class = type(
        cls.__name__,
        (cls,),
        {
            "__init__": __init__,
            "get_instance": classmethod(get_instance),
            **cls.__dict__,
        },
    )

    return new_class
