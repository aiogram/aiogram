"""
Trace hook: one span per dispatch stage, shared by the testing toolkit, OpenTelemetry and logging.

Calling rules (R23), implemented by :func:`enter_spans` / :func:`exit_spans`:

1. For each tracer in order, ``tracer.span(kind, **attrs)`` is called and the result is
   entered manually. If either raises, the failure is logged and that tracer is skipped;
   it is never exited.
2. The caller runs the stage.
3. Each non-``None`` span gets a ``result`` (short string) or ``exception`` (the exception object)
   attribute. A failing ``set_attribute`` is logged and ignored.
4. ``__exit__`` is called in reverse order. Its return value is ignored; a raising ``__exit__``
   is logged and the remaining exits still run.
5. The caller returns the stage result or re-raises the original exception, so a tracer can
   never suppress or replace an application error.

Callers wrap a stage like this::

    entered = enter_spans(tracers, SpanKind.HANDLER, attrs)
    try:
        result = await stage()
    except BaseException as e:
        exit_spans(entered, exception=e)
        raise
    exit_spans(entered, result=result)
    return result

Attribute keys used by aiogram: ``update_id``, ``update_type``, ``bot_id``, ``router``,
``handler``, ``middleware``, ``filter``, ``method``, ``phase``, ``isolation_wait_ms``,
``result``, ``exception``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from enum import StrEnum
from typing import Any, Protocol

from aiogram.dispatcher.event.bases import REJECTED, UNHANDLED, SkipHandler
from aiogram.loggers import dispatcher as logger

__all__ = (
    "CallbackTracer",
    "DispatchTracer",
    "Span",
    "SpanKind",
)


class SpanKind(StrEnum):
    UPDATE = "update"
    ROUTER = "router"
    OUTER_MIDDLEWARE = "outer_middleware"
    FILTER = "filter"
    INNER_MIDDLEWARE = "inner_middleware"
    HANDLER = "handler"
    API_CALL = "api_call"
    TEARDOWN = "teardown"


class Span(Protocol):
    def set_attribute(self, key: str, value: Any) -> None: ...


class DispatchTracer(Protocol):
    def span(self, kind: SpanKind, **attrs: Any) -> AbstractContextManager[Span | None]: ...


def _result_name(result: Any) -> str:
    if result is UNHANDLED:
        return "unhandled"
    if result is REJECTED:
        return "rejected"
    return type(result).__name__


def enter_spans(
    tracers: Iterable[DispatchTracer],
    kind: SpanKind,
    attrs: dict[str, Any],
) -> list[Any]:
    """
    Open one span per tracer. Returns the entered spans for :func:`exit_spans`.
    """
    # ponytail: flat [exit, span, exit, span, ...] keeps it to one allocation per stage
    entered: list[Any] = []
    for tracer in tracers:
        try:
            cm = tracer.span(kind, **attrs)
            exit_ = cm.__exit__
            span = cm.__enter__()  # noqa: PLC2801 - manual enter, see R23
        except BaseException:
            logger.exception("Tracer %r failed to open a %s span", tracer, kind)
            continue
        entered.append(exit_)
        entered.append(span)
    return entered


def exit_spans(
    entered: list[Any],
    result: Any = None,
    exception: BaseException | None = None,
) -> None:
    """
    Close the spans opened by :func:`enter_spans` in reverse order. Never raises.
    """
    # ponytail: tracer failures are contained as BaseException, so a tracer's own
    # KeyboardInterrupt/SystemExit is logged and dropped; narrow it if that ever bites
    value: Any
    if exception is None:
        key, value, exc_type, tb = "result", _result_name(result), None, None
    else:
        if isinstance(exception, SkipHandler):
            key, value = "result", "skip"
        else:
            key, value = "exception", exception
        exc_type, tb = type(exception), exception.__traceback__

    for i in range(len(entered) - 2, -1, -2):
        exit_, span = entered[i], entered[i + 1]
        if span is not None:
            try:
                span.set_attribute(key, value)
            except BaseException:
                logger.exception("Tracer span %r failed to set attribute %r", span, key)
        try:
            exit_(exc_type, exception, tb)
        except BaseException:
            logger.exception("Tracer span %r failed to exit", span)

    if exception is not None and exception.__traceback__ is not tb:
        # A tracer that re-raised the original from __exit__ extended its traceback
        exception.__traceback__ = tb


class _CallbackSpan:
    __slots__ = ("attrs", "kind", "tracer")

    def __init__(self, tracer: CallbackTracer, kind: SpanKind, attrs: dict[str, Any]) -> None:
        self.tracer = tracer
        self.kind = kind
        self.attrs = attrs

    def set_attribute(self, key: str, value: Any) -> None:
        self.attrs[key] = value

    def __enter__(self) -> _CallbackSpan:
        if self.tracer.on_enter is not None:
            self.tracer.on_enter(self.kind, self.attrs)
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, tb: Any) -> None:
        result = self.attrs.pop("result", None)
        self.attrs.pop("exception", None)
        if self.tracer.on_exit is not None:
            self.tracer.on_exit(self.kind, self.attrs, result, exc)


class CallbackTracer:
    """
    Adapter for callback-style consumers.

    :param on_enter: called as ``on_enter(kind, attrs)`` when a span opens
    :param on_exit: called as ``on_exit(kind, attrs, result, exception)`` when it closes;
        ``result`` is the short result string (``"skip"`` for :class:`SkipHandler`,
        ``None`` for any other exception) and
        ``exception`` is the exception the stage raised (``None`` on success).
        ``attrs`` holds the span attributes, without ``result`` and ``exception``.
    """

    def __init__(
        self,
        on_enter: Callable[[SpanKind, dict[str, Any]], Any] | None = None,
        on_exit: Callable[[SpanKind, dict[str, Any], str | None, BaseException | None], Any]
        | None = None,
    ) -> None:
        self.on_enter = on_enter
        self.on_exit = on_exit

    def span(self, kind: SpanKind, **attrs: Any) -> _CallbackSpan:
        return _CallbackSpan(self, kind, attrs)
