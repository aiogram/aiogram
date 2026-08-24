from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.methods import TelegramMethod


@dataclass
class Outcome:
    """A declared answer for a method: either a result or an error."""

    result: Any = None
    error: type[TelegramAPIError] | TelegramAPIError | None = None
    message: str = "Bad Request: test error"
    remaining: int | None = None

    def consume(self) -> None:
        if self.remaining is not None:
            self.remaining -= 1

    @property
    def exhausted(self) -> bool:
        return self.remaining is not None and self.remaining <= 0

    def apply(self, method: TelegramMethod[Any]) -> Any:
        if self.error is None:
            return self.result
        if isinstance(self.error, TelegramAPIError):
            raise self.error
        raise self.error(method=method, message=self.message)


class OverrideRegistry:
    """Per-environment store of declared outcomes, consulted before anything else."""

    def __init__(self) -> None:
        self._outcomes: dict[type[TelegramMethod[Any]], list[Outcome]] = {}

    def add(self, method_type: type[TelegramMethod[Any]], outcome: Outcome) -> None:
        self._outcomes.setdefault(method_type, []).append(outcome)

    def take(self, method: TelegramMethod[Any]) -> Outcome | None:
        for method_type, outcomes in self._outcomes.items():
            if not isinstance(method, method_type):
                continue
            while outcomes:
                outcome = outcomes[0]
                if outcome.exhausted:
                    outcomes.pop(0)
                    continue
                outcome.consume()
                if outcome.exhausted:
                    outcomes.pop(0)
                return outcome
        return None

    def clear(self) -> None:
        self._outcomes.clear()


class OverrideBuilder:
    """Fluent handle returned by ``environment.on(Method)``."""

    def __init__(
        self,
        registry: OverrideRegistry,
        method_type: type[TelegramMethod[Any]],
    ) -> None:
        self._registry = registry
        self._method_type = method_type

    def returns(self, result: Any, *, times: int | None = None) -> OverrideBuilder:
        self._registry.add(self._method_type, Outcome(result=result, remaining=times))
        return self

    def raises(
        self,
        error: type[TelegramAPIError] | TelegramAPIError = TelegramBadRequest,
        message: str = "Bad Request: test error",
        *,
        times: int | None = None,
    ) -> OverrideBuilder:
        self._registry.add(
            self._method_type,
            Outcome(error=error, message=message, remaining=times),
        )
        return self
