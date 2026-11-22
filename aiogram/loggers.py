"""
Framework loggers and the per-update log context.

This module is the only place aiogram creates loggers: every framework logger comes from
:func:`get_logger`, which installs the framework record filters on it. Python never runs an
ancestor logger's filters for a child's records, so each logger carries its own.

Inside :meth:`Dispatcher.feed_update <aiogram.dispatcher.dispatcher.Dispatcher.feed_update>` every
framework record gets six attributes (``None`` when unknown, so format strings never raise):
``aiogram_bot_id``, ``aiogram_update_id``, ``aiogram_update_type``, ``aiogram_router``,
``aiogram_handler``, ``aiogram_phase``. :func:`context_filter` attaches them to any other record.

Every framework logger also carries a :class:`TokenRedactingFilter`, which masks bot tokens as
``<bot id>:***``. It is on by default; :func:`redact_tokens` turns it off and on.
"""

from __future__ import annotations

import contextlib
import logging
import re
import traceback
import warnings
from contextvars import ContextVar
from typing import Any

__all__ = (
    "TokenRedactingFilter",
    "client",
    "context_filter",
    "dispatcher",
    "event",
    "fsm",
    "get_logger",
    "i18n",
    "middlewares",
    "polling",
    "redact_tokens",
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


# A bot token: the numeric bot id, ``:``, the secret; masked as ``<bot id>:***``. No leading
# ``\b``: in a URL the id follows ``bot`` (``/bot123456:...``) with no word boundary between.
_TOKEN_PATTERN = re.compile(r"(\d{5,}):[A-Za-z0-9_-]{30,}")
_enabled = True
_warned = False
# Attributes every record has; anything else came from ``extra=`` or a formatter (``message``)
_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)


def _redact(text: str) -> str | None:
    """Return ``text`` with every token masked, or ``None`` when it holds no token."""
    redacted, count = _TOKEN_PATTERN.subn(r"\1:***", text)
    return redacted if count else None


def redact_tokens(enabled: bool) -> None:
    """
    Turn token redaction on or off for every :class:`TokenRedactingFilter` at once.

    Redaction is on by default.

    :param enabled: :code:`False` lets records through unchanged
    """
    global _enabled  # noqa: PLW0603
    _enabled = enabled


class TokenRedactingFilter(logging.Filter):
    """
    Mask bot tokens (``123456:AA...`` becomes ``123456:***``) in a log record.

    It scans the formatted message, the exception and stack text, and string attributes added
    with ``extra=`` (one level of ``dict`` values included). A record without a token is left
    untouched. The filter never drops a record and never raises.

    Framework loggers carry it already; attach it to a handler to cover other records::

        handler.addFilter(aiogram.loggers.TokenRedactingFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if _enabled:
            try:
                _redact_record(record)
            except Exception as e:  # noqa: BLE001
                _warn_once(e)
        return True


def _redact_record(record: logging.LogRecord) -> None:
    try:
        message = record.getMessage()
    except Exception:  # noqa: BLE001
        pass  # a malformed record: the handler reports it through handleError
    else:
        if (redacted := _redact(message)) is not None:
            record.msg, record.args = redacted, ()
    exc_text = record.exc_text
    if not exc_text and record.exc_info and record.exc_info[1] is not None:
        exc_text = "".join(traceback.format_exception(*record.exc_info)).rstrip("\n")
    # Written only on a match, so a formatter's own formatException keeps ordinary records
    if exc_text and (redacted := _redact(exc_text)) is not None:
        record.exc_text = redacted
    if record.stack_info and (redacted := _redact(record.stack_info)) is not None:
        record.stack_info = redacted
    attrs = record.__dict__
    for key in attrs.keys() - _RECORD_ATTRS:  # a set difference, so the writes below are safe
        value = attrs[key]
        if isinstance(value, str):
            if (redacted := _redact(value)) is not None:
                attrs[key] = redacted
        elif isinstance(value, dict) and (copy := _redact_dict(value)) is not None:
            attrs[key] = copy


def _redact_dict(value: dict[Any, Any]) -> dict[Any, Any] | None:
    """Return a copy of ``value`` with its string values masked, or ``None`` when none matched."""
    copy: dict[Any, Any] | None = None
    for key, item in value.items():
        if isinstance(item, str) and (redacted := _redact(item)) is not None:
            if copy is None:
                copy = dict(value)  # never mutate the caller's dict
            copy[key] = redacted
    return copy


def _warn_once(error: Exception) -> None:
    global _warned  # noqa: PLW0603
    if _warned:
        return
    _warned = True
    # ``-W error`` makes the warning raise; filter() still must not. Not reported through
    # logging: that would run this filter again.
    with contextlib.suppress(Exception):
        warnings.warn(
            f"aiogram token redaction failed, record passed unchanged: {error!r}",
            RuntimeWarning,
            stacklevel=2,
        )


_REDACTING_FILTER = TokenRedactingFilter()
_REDACTING_FILTER.aiogram_framework_filter = True  # type: ignore[attr-defined]
_FRAMEWORK_FILTERS = (_CONTEXT_FILTER, _REDACTING_FILTER)


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
        if stale not in _FRAMEWORK_FILTERS:
            logger.removeFilter(stale)
    # Context first, so the redaction scans the context attributes too; no-op when installed
    for framework_filter in _FRAMEWORK_FILTERS:
        logger.addFilter(framework_filter)
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
