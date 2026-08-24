from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from .errors import WaitTimeoutError

__all__ = ("describe_callable", "poll_until")


async def poll_until(
    predicate: Callable[[], object | Awaitable[object]],
    *,
    timeout: float,
    interval: float,
    describe_timeout: Callable[[], str],
) -> Any:
    """
    Re-run ``predicate`` until it produces something truthy, and return that value.

    The polling core of the toolkit's waiting helpers. It lives in a module of its own
    because both ends use it — :meth:`aiogram.test.BotTestEnvironment.wait_for` and
    :meth:`aiogram.test.world.ChatState.wait_for_message` — while
    :mod:`aiogram.test.world` must not import :mod:`aiogram.test.environment`.

    ``predicate`` may be synchronous or return an awaitable; both are supported so that a
    test can wait on a coroutine reading the state under test. It is checked once before
    any sleeping, so an already-satisfied wait costs nothing, and once more after the
    deadline has passed, so a change that lands exactly on the deadline still counts.

    Sleeping between checks is what makes this useful at all: the bot's own background
    tasks only run while the test yields to the event loop.

    ``describe_timeout`` builds the failure message and is called only when the wait
    actually fails, so an expensive description costs nothing on the happy path.
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        result = predicate()
        if inspect.isawaitable(result):
            result = await result
        if result:
            return result
        if loop.time() >= deadline:
            raise WaitTimeoutError(describe_timeout())
        await asyncio.sleep(interval)


def describe_callable(target: object) -> str:
    """Best-effort identification of a predicate for a failure message."""
    name = getattr(target, "__qualname__", None)
    if isinstance(name, str) and name:
        return name
    return repr(target)
