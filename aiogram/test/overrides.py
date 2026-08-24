from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.methods import TelegramMethod

from .mounting import bindables


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
            return fresh_result(self.result)
        if isinstance(self.error, TelegramAPIError):
            raise self.error
        raise self.error(method=method, message=self.message)


def fresh_result(result: Any) -> Any:
    """
    Hand out a copy of a declared result, unbound, the way a real answer is freshly parsed.

    The declared object belongs to the test — it is often built once at module level and
    reused — while the answer belongs to the caller: it gets mounted to the calling bot,
    and a modeled follow-up may edit it. Returning the very object the test declared would
    mean the test's own object is mutated by the call it describes, and that it holds a
    reference to every :class:`~aiogram.client.bot.Bot` that ever received it, long after
    those environments were disposed. Copying also makes a repeated override (``times=None``)
    behave like the API it stands in for: each call gets its own response.

    Copying deeply, but never following a binding: ``_bot`` is a live bot with a session,
    a world and a dispatcher behind it, so the memo maps every bot already in the graph to
    itself. The copy is then handed over unbound, leaving
    :func:`aiogram.test.mounting.mount` to bind it to whoever asked, exactly as it does for
    a modeled or synthesized answer.
    """
    if isinstance(result, list):
        return [fresh_result(item) for item in result]
    if isinstance(result, tuple):
        return tuple(fresh_result(item) for item in result)
    if not isinstance(result, BaseModel):
        # `bool`, `int`, `str` and friends are the common case, and immutable anyway.
        return result

    memo: dict[int, Any] = {
        id(node.bot): node.bot for node in bindables(result) if node.bot is not None
    }
    copied = copy.deepcopy(result, memo)
    for node in bindables(copied):
        node.as_(None)
    return copied


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
