from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from aiogram.methods import TelegramMethod

MethodT = TypeVar("MethodT", bound=TelegramMethod[Any])


class NoSuchCallError(AssertionError):
    """Raised when the call log is asked for a call that was never made."""


class CallLog:
    """Ordered log of every Bot API call made inside an environment."""

    def __init__(self) -> None:
        self._entries: list[TelegramMethod[Any]] = []

    def record(self, method: TelegramMethod[Any]) -> None:
        self._entries.append(method)

    @property
    def entries(self) -> list[TelegramMethod[Any]]:
        return list(self._entries)

    def all(self, method_type: type[MethodT]) -> list[MethodT]:
        return [entry for entry in self._entries if isinstance(entry, method_type)]

    def last(self, method_type: type[MethodT]) -> MethodT:
        calls = self.all(method_type)
        if not calls:
            msg = (
                f"No {method_type.__name__} call was made. "
                f"Recorded calls: {self.summary() or 'none'}"
            )
            raise NoSuchCallError(msg)
        return calls[-1]

    def first(self, method_type: type[MethodT]) -> MethodT:
        calls = self.all(method_type)
        if not calls:
            msg = (
                f"No {method_type.__name__} call was made. "
                f"Recorded calls: {self.summary() or 'none'}"
            )
            raise NoSuchCallError(msg)
        return calls[0]

    def count(self, method_type: type[TelegramMethod[Any]] | None = None) -> int:
        if method_type is None:
            return len(self._entries)
        return sum(1 for entry in self._entries if isinstance(entry, method_type))

    def filter(
        self,
        predicate: Callable[[TelegramMethod[Any]], bool],
    ) -> list[TelegramMethod[Any]]:
        return [entry for entry in self._entries if predicate(entry)]

    def summary(self) -> str:
        return ", ".join(type(entry).__name__ for entry in self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[TelegramMethod[Any]]:
        return iter(self._entries)

    def __bool__(self) -> bool:
        return bool(self._entries)

    def __repr__(self) -> str:
        return f"<CallLog {len(self._entries)} calls: {self.summary()}>"
