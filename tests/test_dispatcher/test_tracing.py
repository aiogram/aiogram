import asyncio
import logging
from typing import Any

import pytest

from aiogram.dispatcher import CallbackTracer, SpanKind
from aiogram.dispatcher.event.bases import REJECTED, UNHANDLED, SkipHandler
from aiogram.dispatcher.tracing import enter_spans, exit_spans


class Result:
    pass


class AppError(Exception):
    pass


class TracerError(Exception):
    pass


class RecordingTracer:
    def __init__(self, name: str, events: list[tuple[str, str]], failure: str | None) -> None:
        self.name = name
        self.events = events
        self.failure = failure
        self.attrs: dict[str, Any] = {}
        self.exit_args: tuple[Any, ...] | None = None

    def span(self, kind: SpanKind, **attrs: Any) -> "RecordingTracer":
        if self.failure == "span":
            raise TracerError(self.name)
        self.attrs.update(attrs)
        return self

    def set_attribute(self, key: str, value: Any) -> None:
        if self.failure == "set_attribute":
            raise TracerError(self.name)
        self.attrs[key] = value

    def __enter__(self) -> "RecordingTracer | None":
        if self.failure == "enter":
            raise TracerError(self.name)
        self.events.append(("enter", self.name))
        return None if self.failure == "none_span" else self

    def __exit__(self, *args: Any) -> bool:
        self.events.append(("exit", self.name))
        self.exit_args = args
        if self.failure == "exit":
            raise args[1] if args[1] is not None else TracerError(self.name)
        if self.failure == "exit_other":
            raise TracerError(self.name)
        return self.failure == "exit_true"


def run(tracers: list[Any], outcome: Any) -> Any:
    """The caller pattern from the tracing module docstring, with a sync stage."""
    entered = enter_spans(tracers, SpanKind.HANDLER, {"handler": "h"})
    try:
        if isinstance(outcome, BaseException):
            raise outcome
        result = outcome
    except BaseException as e:
        exit_spans(entered, exception=e)
        raise
    exit_spans(entered, result=result)
    return result


def tracer_logs(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "aiogram.dispatcher"]


def tb_chain(tb: Any) -> list[Any]:
    chain = []
    while tb is not None:
        chain.append(tb)
        tb = tb.tb_next
    return chain


LOGGED = {"span", "enter", "exit", "exit_other", "set_attribute"}
NOT_ENTERED = {"span", "enter"}


@pytest.mark.parametrize("count", [1, 3])
@pytest.mark.parametrize(
    "failure",
    ["span", "enter", "exit", "exit_true", "exit_other", "set_attribute", "none_span", None],
)
@pytest.mark.parametrize("outcome_type", [Result, AppError, asyncio.CancelledError])
def test_failure_matrix(
    caplog: pytest.LogCaptureFixture,
    count: int,
    failure: str | None,
    outcome_type: type,
) -> None:
    caplog.set_level(logging.DEBUG)
    events: list[tuple[str, str]] = []
    bad = count // 2
    tracers = [
        RecordingTracer(str(i), events, failure if i == bad else None) for i in range(count)
    ]
    outcome = outcome_type()

    if isinstance(outcome, BaseException):
        with pytest.raises(outcome_type) as exc_info:
            run(tracers, outcome)
        assert exc_info.value is outcome
    else:
        assert run(tracers, outcome) is outcome

    entered = [t.name for t in tracers if t.failure not in NOT_ENTERED]
    assert events == [("enter", n) for n in entered] + [("exit", n) for n in reversed(entered)]

    logs = tracer_logs(caplog)
    assert len(logs) == (1 if failure in LOGGED else 0)
    assert all(r.exc_info is not None for r in logs)

    for t in tracers:
        if t.failure in NOT_ENTERED:
            assert t.exit_args is None
            continue
        assert t.exit_args is not None
        if isinstance(outcome, BaseException):
            assert t.exit_args[:2] == (outcome_type, outcome)
            assert t.exit_args[2] in tb_chain(outcome.__traceback__)
        else:
            assert t.exit_args == (None, None, None)
        if t.failure in {"set_attribute", "none_span"}:
            assert "result" not in t.attrs
            assert "exception" not in t.attrs
        elif isinstance(outcome, BaseException):
            assert t.attrs["exception"] is outcome
        else:
            assert t.attrs["result"] == "Result"
        assert t.attrs["handler"] == "h"


def test_reraising_exit_keeps_traceback() -> None:
    tracer = RecordingTracer("0", [], "exit")
    error = AppError()
    entered = enter_spans([tracer], SpanKind.HANDLER, {})
    try:
        raise error
    except AppError as e:
        tb = e.__traceback__
        exit_spans(entered, exception=e)
    assert error.__traceback__ is tb


@pytest.mark.parametrize(
    ("result", "expected"),
    [(UNHANDLED, "unhandled"), (REJECTED, "rejected"), (None, "NoneType"), (42, "int")],
)
def test_result_names(result: Any, expected: str) -> None:
    tracer = RecordingTracer("0", [], None)
    exit_spans(enter_spans([tracer], SpanKind.FILTER, {}), result=result)
    assert tracer.attrs["result"] == expected


def test_skip_handler_is_result() -> None:
    tracer = RecordingTracer("0", [], None)
    error = SkipHandler()
    exit_spans(enter_spans([tracer], SpanKind.HANDLER, {}), exception=error)
    assert tracer.attrs == {"result": "skip"}
    assert tracer.exit_args is not None
    assert tracer.exit_args[1] is error


class TestCallbackTracer:
    def test_success(self) -> None:
        calls: list[tuple[Any, ...]] = []
        tracer = CallbackTracer(
            on_enter=lambda kind, attrs: calls.append(("enter", kind, dict(attrs))),
            on_exit=lambda kind, attrs, result, exc: calls.append(
                ("exit", kind, dict(attrs), result, exc)
            ),
        )
        assert run([tracer], Result()).__class__ is Result
        assert calls == [
            ("enter", SpanKind.HANDLER, {"handler": "h"}),
            ("exit", SpanKind.HANDLER, {"handler": "h"}, "Result", None),
        ]

    def test_exception(self) -> None:
        calls: list[tuple[Any, ...]] = []
        tracer = CallbackTracer(
            on_exit=lambda kind, attrs, result, exc: calls.append((kind, attrs, result, exc))
        )
        error = AppError()
        with pytest.raises(AppError):
            run([tracer], error)
        assert calls == [(SpanKind.HANDLER, {"handler": "h"}, None, error)]

    def test_no_callbacks(self) -> None:
        assert run([CallbackTracer()], 1) == 1

    def test_callback_failure_is_contained(self, caplog: pytest.LogCaptureFixture) -> None:
        def boom(*args: Any) -> None:
            raise TracerError

        error = AppError()
        with pytest.raises(AppError) as exc_info:
            run([CallbackTracer(on_enter=boom), CallbackTracer(on_exit=boom)], error)
        assert exc_info.value is error
        assert len(tracer_logs(caplog)) == 2
