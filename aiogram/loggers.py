"""
Framework loggers and the per-update log context.

This module is the only place aiogram creates loggers: every framework logger comes from
:func:`get_logger`, which installs the framework record filters on it. Python never runs an
ancestor logger's filters for a child's records, so each logger carries its own.

Inside :meth:`Dispatcher.feed_update <aiogram.dispatcher.dispatcher.Dispatcher.feed_update>` every
framework record gets six attributes (``None`` when unknown, so format strings never raise):
``aiogram_bot_id``, ``aiogram_update_id``, ``aiogram_update_type``, ``aiogram_router``,
``aiogram_handler``, ``aiogram_phase``. :func:`context_filter` attaches them to any other record.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

__all__ = (
    "client",
    "context_filter",
    "dispatcher",
    "event",
    "fsm",
    "get_logger",
    "i18n",
    "middlewares",
    "polling",
    "runner",
    "scene",
    "webhook",
)


class LogContext:
    """
    Per-update log context (internal).

    One object per update, set by ``Dispatcher.feed_update``. ``router``, ``handler`` and
    ``phase`` are plain attribute writes, so the executor updates them without a
    ``ContextVar.set`` per stage. Tasks started during the update share the object, so their
    records show the update's current stage.
    """

    __slots__ = ("bot_id", "handler", "phase", "router", "update_id", "update_type")

    def __init__(self, bot_id: int | None, update_id: int | None, update_type: str | None) -> None:
        self.bot_id = bot_id
        self.update_id = update_id
        self.update_type = update_type
        self.router: str | None = None
        self.handler: str | None = None
        self.phase: str | None = None


_NO_CONTEXT = LogContext(None, None, None)
_current: ContextVar[LogContext | None] = ContextVar("aiogram_log_context", default=None)


def _log_context() -> LogContext | None:
    """Return the log context of the update being processed, or ``None`` outside an update."""
    return _current.get()


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _current.get() or _NO_CONTEXT
        attrs = record.__dict__
        # setdefault: an attribute passed explicitly with ``extra=`` wins
        attrs.setdefault("aiogram_bot_id", ctx.bot_id)
        attrs.setdefault("aiogram_update_id", ctx.update_id)
        attrs.setdefault("aiogram_update_type", ctx.update_type)
        attrs.setdefault("aiogram_router", ctx.router)
        attrs.setdefault("aiogram_handler", ctx.handler)
        attrs.setdefault("aiogram_phase", ctx.phase)
        return True


_CONTEXT_FILTER = _ContextFilter()
# Marks the instances the factory installs, so a re-import of this module (``importlib.reload``,
# a coverage run on this one module) replaces them instead of stacking a stale copy.
_CONTEXT_FILTER.aiogram_framework_filter = True  # type: ignore[attr-defined]


def context_filter() -> logging.Filter:
    """
    Return a filter that copies the aiogram log context onto any record.

    Attach it to a user logger or handler::

        handler.addFilter(aiogram.loggers.context_filter())
    """
    return _ContextFilter()


def get_logger(name: str) -> logging.Logger:
    """
    Return the framework logger ``name`` with the framework record filters installed.

    :param name: logger name, must start with ``aiogram.``
    """
    if not name.startswith("aiogram."):
        msg = f"aiogram logger names start with 'aiogram.', got {name!r}"
        raise ValueError(msg)
    logger = logging.getLogger(name)
    for stale in [f for f in logger.filters if getattr(f, "aiogram_framework_filter", False)]:
        if stale is not _CONTEXT_FILTER:
            logger.removeFilter(stale)
    logger.addFilter(_CONTEXT_FILTER)  # no-op when already installed
    return logger


dispatcher = get_logger("aiogram.dispatcher")
runner = get_logger("aiogram.runner")
polling = get_logger("aiogram.polling")
webhook = get_logger("aiogram.webhook")
client = get_logger("aiogram.client")
fsm = get_logger("aiogram.fsm")
scene = get_logger("aiogram.scene")
i18n = get_logger("aiogram.i18n")
event = get_logger("aiogram.event")
# Request records stay here for one deprecation window, then move to ``client``.
middlewares = get_logger("aiogram.middlewares")
