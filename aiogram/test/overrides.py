from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.methods import TelegramMethod

from .mounting import detached_copy

if TYPE_CHECKING:
    from aiogram.client.bot import Bot


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

    def apply(self, method: TelegramMethod[Any], bot: Bot | None = None) -> Any:
        """
        The declared answer, as a fresh object bound to whoever asked for it.

        The declared object belongs to the test — it is often built once at module level
        and reused — while the answer belongs to the caller: it gets mounted to the calling
        bot, and a modeled follow-up may edit it. Handing out the very object the test
        declared would mean the test's own object is mutated by the call it describes, and
        that it holds a reference to every :class:`~aiogram.client.bot.Bot` that ever
        received it, long after those environments were disposed. Copying also makes a
        repeated override (``times=None``) behave like the API it stands in for: each call
        gets its own response.

        The caller's bot is known here, so the copy is bound as it is made and the session's
        own :func:`~aiogram.test.mounting.mount` prunes at its root — one walk instead of a
        walk to bind, a walk to unbind, and a walk to bind again.
        """
        if self.error is None:
            return detached_copy(self.result, bot=bot)
        if isinstance(self.error, TelegramAPIError):
            raise self.error
        raise self.error(method=method, message=self.message)


def fresh_result(result: Any) -> Any:
    """
    A copy of a declared result, unbound, the way a real answer is freshly parsed.

    Kept as the name for the unbound half of :meth:`Outcome.apply`; the policy itself lives
    in :func:`aiogram.test.mounting.detached_copy`.
    """
    return detached_copy(result)


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
