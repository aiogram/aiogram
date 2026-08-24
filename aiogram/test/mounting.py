from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from aiogram.client.context_controller import BotContextController

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

__all__ = ("bindables", "mount")


def mount(value: Any, bot: Bot) -> Any:
    """
    Bind every *unbound* object reachable from ``value`` to ``bot``, and return ``value``.

    A real session deserializes every response with ``context={"bot": bot}``, which pydantic
    threads through the whole object tree — so ``message.delete()``, ``message.answer()``
    and the shortcuts of nested objects such as ``message.reply_to_message`` all work on
    whatever a Bot API call returned.

    The fake world hands back objects that were *constructed*, not parsed, so that context
    never runs and every shortcut on them would raise. Re-parsing them to reuse pydantic's
    mechanism is not an option: pydantic skips validation of model instances
    (``revalidate_instances`` is ``"never"``), so binding would require a dump/validate
    round-trip — which mints copies, severing the identity between a returned message and
    the one the world keeps, and quietly reshapes unions and sentinel defaults along the
    way. Walking the tree and calling
    :meth:`~aiogram.client.context_controller.BotContextController.as_` mirrors what the
    context does while leaving the objects themselves untouched.

    This is the toolkit's single binding mechanism. It runs at every point where an object
    enters the fake world or leaves it towards the code under test: when a chat stores a
    message (:meth:`aiogram.test.world.ChatState.add_message`), when an update is fed
    (:meth:`aiogram.test.BotTestEnvironment.feed`) and when a call is answered
    (:meth:`aiogram.test.FakeTelegramSession.make_request`).

    **Ownership rule: an object that already carries a bot is left alone, and the walk
    stops there.** Because everything is bound the moment it enters the world, an object
    that is already bound belongs to the environment, and a later caller must not claim it.
    That matters as soon as a *second* :class:`~aiogram.client.bot.Bot` shares the session
    — the documented recipe for testing a bot that sends through a module-level instance:
    rebinding a stored message to it would silently change which
    :class:`~aiogram.client.default.DefaultBotProperties` every later shortcut on that
    message resolves against. Only genuinely fresh objects, minted for this very call, are
    bound to the caller.

    Pruning is what keeps the walk cheap, too: re-answering with a stored message stops the
    walk at that message instead of re-walking everything it transitively refers to.
    """
    for node in bindables(value, prune_bound=True):
        node.as_(bot)
    return value


def bindables(value: Any, *, prune_bound: bool = False) -> Iterator[BotContextController]:
    """
    Walk the object graph of ``value``, yielding every bindable object it reaches.

    The walk is iterative rather than recursive because the graphs are not shallow: the
    fake nests ``reply_to_message`` as deep as a reply chain is long, and a recursive
    walker hit Python's recursion limit on chains a test can plausibly build.

    ``prune_bound`` stops the walk at objects that already carry a bot — see :func:`mount`
    for why that is the correct ownership rule and not merely an optimization.
    """
    seen: set[int] = set()
    stack: list[Any] = [value]
    while stack:
        current = stack.pop()
        # Cheap rejection first: results are most often `bool`, `int` or `str`.
        if current is None or isinstance(current, (str, bytes, int, float)):
            continue

        identity = id(current)
        if identity in seen:
            # The world stores objects by reference, so the same `Chat` shows up on every
            # message of a chat, and a message may transitively refer back to itself.
            continue
        seen.add(identity)

        if isinstance(current, BaseModel):
            if isinstance(current, BotContextController):
                if prune_bound and current.bot is not None:
                    continue
                yield current
            # `__dict__` holds the validated fields; `extra="allow"` parks unknown ones,
            # which may carry objects from a future Bot API version, in
            # `__pydantic_extra__`.
            stack.extend(current.__dict__.values())
            stack.extend((current.__pydantic_extra__ or {}).values())
        elif isinstance(current, Mapping):
            stack.extend(current.values())
        elif isinstance(current, Iterable):
            # Nested lists are real: `InlineKeyboardMarkup.inline_keyboard` is a list of rows.
            stack.extend(current)
