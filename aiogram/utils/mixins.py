import contextvars
from typing import TypeVar, Type

__all__ = ('DataMixin', 'ContextInstanceMixin')


class DataMixin:
    @property
    def data(self):
        data = getattr(self, '_data', None)
        if data is None:
            data = {}
            setattr(self, '_data', data)
        return data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)


T = TypeVar('T')


class ContextInstanceMixin:
    def __init_subclass__(cls, **kwargs):
        cls.__context_instance = contextvars.ContextVar('instance_' + cls.__name__)
        return cls

    @classmethod
    def get_current(cls: Type[T], no_error=True) -> T:
        if no_error:
            return cls.__context_instance.get(None)
        return cls.__context_instance.get()

    @classmethod
    def set_current(cls: Type[T], value: T):
        if not isinstance(value, cls):
            raise TypeError(f"Value should be instance of '{cls.__name__}' not '{type(value).__name__}'")
        cls.__context_instance.set(value)
