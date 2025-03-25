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
    """
    Singleton Decorator for classes
    The decorated class has to be instantiated with cls.get_instance(*args, **kwargs)
    The Metaclass approach causes conflicts with other metaclasses of a class
    We also cannot override __new__ method because it can be
    defined in the decorated class or the parent class
    """
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
