"""
Typed views of the data that middlewares, filters and handlers receive (D31).

Keys become available at different points of an update's path, so there is one type per point:

- :class:`OuterData`: ``dp.update`` outer middlewares, and everything on the ``dp.update``
  observer itself (its filters, inner middlewares and handlers) and ``errors`` handlers, which see
  some routing keys but not all of them (read those with ``.get``);
- :class:`RouterOuterData`: router-level outer middlewares (``router.message.outer_middleware``);
- :class:`AiogramData`: inner middlewares, filters and handlers of the event observers
  (``router.message``, ``router.callback_query``, ...).

Extend the one you need with your own keys, e.g. ``class AppData(AiogramData): db: Database``,
and use it as ``**kw: Unpack[AppData]`` in a handler. This module is typing only: nothing here
changes what is injected.
"""

# No `from __future__ import annotations`: it hides NotRequired from __required_keys__ at runtime
import warnings
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

if TYPE_CHECKING:
    from aiogram import Bot, Dispatcher, Router
    from aiogram.dispatcher.event.handler import HandlerObject
    from aiogram.dispatcher.middlewares.user_context import EventContext
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import BaseStorage
    from aiogram.types import Update
    from aiogram.utils.i18n import I18n, I18nMiddleware

__all__ = ("AiogramData", "FSMKeysData", "OuterData", "RouterOuterData")


class OuterData(TypedDict):
    """
    Data available to ``dp.update`` outer middlewares.

    Also the type to use on the ``dp.update`` observer itself (filters, inner middlewares,
    handlers) and in ``errors`` handlers: they never get ``event_update``.
    """

    dispatcher: "Dispatcher"
    """Dispatcher that is handling the update."""
    bot: "Bot"
    """Bot that received the update."""
    event_context: "EventContext"
    """User, chat and thread of the update, set by the built-in user context middleware."""
    bots: NotRequired["tuple[Bot, ...]"]
    """All bots of the polling loop. Set only in polling mode."""
    fsm_storage: NotRequired["BaseStorage"]
    """FSM storage. Absent when the dispatcher was created with ``disable_fsm=True``."""


class FSMKeysData(TypedDict):
    """
    Keys set by the built-in FSM middleware.

    ``state`` and ``raw_state`` are absent when FSM is disabled or the update has no chat or user
    to key it on.
    """

    fsm_storage: NotRequired["BaseStorage"]
    """FSM storage. Absent when the dispatcher was created with ``disable_fsm=True``."""
    state: NotRequired["FSMContext"]
    """FSM context of the current user and chat."""
    raw_state: NotRequired["str | None"]
    """Current state name as stored."""


class RouterOuterData(OuterData, FSMKeysData):
    """
    Data available to router-level outer middlewares (``router.message.outer_middleware``).
    """

    event_update: "Update"
    """Update that contains the current event."""
    event_router: "Router"
    """Router that is propagating the event."""


class AiogramData(RouterOuterData):
    """
    Data available to inner middlewares, filters and handlers of the event observers
    (``router.message``, ``router.callback_query``, ...), not of ``dp.update``
    (see :class:`OuterData`).
    """

    handler: "HandlerObject"
    """Handler that is being checked or called. In a router's root filters
    (``router.message.filter(...)``) it is still the dispatcher's internal update handler."""
    i18n: NotRequired["I18n"]
    """I18n object. Set only by the i18n middleware with the default ``i18n_key``."""
    i18n_middleware: NotRequired["I18nMiddleware"]
    """The i18n middleware. Set only when it is installed with the default ``middleware_key``."""


if TYPE_CHECKING:
    MiddlewareData = AiogramData
    """Deprecated alias of :class:`AiogramData` (AG4060)."""


def __getattr__(name: str) -> Any:
    if name == "MiddlewareData":
        # ponytail: plain DeprecationWarning until the I-12 AiogramDeprecationWarning class lands
        warnings.warn(
            "AG4060: MiddlewareData is a deprecated alias of AiogramData; "
            "use aiogram.dispatcher.middlewares.data.AiogramData.",
            DeprecationWarning,
            stacklevel=2,
        )
        return AiogramData
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
