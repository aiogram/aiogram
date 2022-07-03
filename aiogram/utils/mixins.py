from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar, cast, overload

if TYPE_CHECKING:
    from typing_extensions import Literal

__all__ = ("ContextInstanceMixin", "DataMixin")


class DataMixin:
    @property
    def data(self) -> Dict[str, Any]:
        data: Optional[Dict[str, Any]] = getattr(self, "_data", None)
        if data is None:
            data = {}
            setattr(self, "_data", data)
        return data

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __delitem__(self, key: str) -> None:
        del self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self.data.get(key, default)


ContextInstance = TypeVar("ContextInstance")


class ContextInstanceMixin(Generic[ContextInstance]):
    __context_instance: contextvars.ContextVar[ContextInstance]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()
        cls.__context_instance = contextvars.ContextVar(f"instance_{cls.__name__}")

    @overload  # noqa: F811
    @classmethod
    def get_current(cls) -> Optional[ContextInstance]:  # pragma: no cover  # noqa: F811
        ...

    @overload  # noqa: F811
    @classmethod
    def get_current(  # noqa: F811
        cls, no_error: Literal[True]
    ) -> Optional[ContextInstance]:  # pragma: no cover  # noqa: F811
        ...

    @overload  # noqa: F811
    @classmethod
    def get_current(  # noqa: F811
        cls, no_error: Literal[False]
    ) -> ContextInstance:  # pragma: no cover  # noqa: F811
        ...

    @classmethod  # noqa: F811
    def get_current(  # noqa: F811
        cls, no_error: bool = True
    ) -> Optional[ContextInstance]:  # pragma: no cover  # noqa: F811
        # on mypy 0.770 I catch that contextvars.ContextVar always contextvars.ContextVar[Any]
        cls.__context_instance = cast(
            contextvars.ContextVar[ContextInstance], cls.__context_instance
        )

        try:
            current: Optional[ContextInstance] = cls.__context_instance.get()
        except LookupError:
            if no_error:
                current = None
            else:
                raise

        return current

    @classmethod
    def set_current(cls, value: ContextInstance) -> contextvars.Token[ContextInstance]:
        if not isinstance(value, cls):
            raise TypeError(
                f"Value should be instance of {cls.__name__!r} not {type(value).__name__!r}"
            )
        return cls.__context_instance.set(value)

    @classmethod
    def reset_current(cls, token: contextvars.Token[ContextInstance]) -> None:
        cls.__context_instance.reset(token)
