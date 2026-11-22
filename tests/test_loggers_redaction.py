import json
import logging
import subprocess
import sys
import time
import traceback
import warnings

import pytest
from yarl import URL

from aiogram import loggers
from tests.token_safety import FAKE_TOKEN

SECRET = FAKE_TOKEN.partition(":")[2]
MASKED = FAKE_TOKEN.partition(":")[0] + ":***"


class _Capture(logging.Handler):
    """Formats each record twice: the standard formatter and a JSON dump of the record."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []
        self.text: list[str] = []
        self.json: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        self.text.append(logging.Formatter("%(message)s").format(record))
        self.json.append(json.dumps(record.__dict__, default=str))

    def output(self) -> str:
        return "\n".join(self.text + self.json)


@pytest.fixture
def capture():
    handler = _Capture()
    targets = [loggers.client, loggers.get_logger("aiogram.client.x")]
    saved = [(target, target.level) for target in targets]
    for target in targets:
        target.addHandler(handler)
        target.setLevel(logging.DEBUG)
    yield handler
    for target, level in saved:
        target.removeHandler(handler)
        target.setLevel(level)


@pytest.fixture(autouse=True)
def _restore_state(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(loggers, "_enabled", True)
    monkeypatch.setattr(loggers, "_warned", False)


def assert_clean(capture: _Capture) -> None:
    out = capture.output()
    assert SECRET not in out, out
    assert MASKED in out, out


def raise_chained() -> None:
    try:
        raise OSError(f"connect to /bot{FAKE_TOKEN}/getMe failed")
    except OSError as e:
        raise RuntimeError("request failed") from e


class TestRedaction:
    @pytest.mark.parametrize("name", ["aiogram.client", "aiogram.client.x"])
    def test_child_loggers(self, capture: _Capture, name: str):
        logging.getLogger(name).info("token %s", FAKE_TOKEN)
        assert_clean(capture)

    @pytest.mark.parametrize(
        "arg",
        [
            URL(f"https://api.telegram.org/bot{FAKE_TOKEN}/getMe"),
            OSError(f"boom /bot{FAKE_TOKEN}/"),
        ],
    )
    def test_non_str_args(self, capture: _Capture, arg: object):
        loggers.client.info("failed: %s", arg)
        record = capture.records[0]
        assert record.args == ()
        assert record.msg.startswith("failed: ")
        assert_clean(capture)

    def test_chained_exception(self, capture: _Capture):
        try:
            raise_chained()
        except RuntimeError:
            loggers.client.exception("request failed")
        assert SECRET not in capture.records[0].exc_text
        full = logging.Formatter().format(capture.records[0])
        assert "OSError" in full
        assert SECRET not in full
        assert MASKED in full

    def test_exc_text_already_formatted(self):
        """A handler-level instance after another handler has cached the traceback."""
        try:
            raise_chained()
        except RuntimeError:
            record = logging.LogRecord("x", 40, "f", 1, "m", (), sys.exc_info())
        logging.Formatter().format(record)  # caches exc_text and sets record.message
        assert SECRET in record.exc_text
        loggers.TokenRedactingFilter().filter(record)
        assert SECRET not in record.exc_text
        assert SECRET not in json.dumps(record.__dict__, default=str)

    def test_extra(self, capture: _Capture):
        nested = {"line": f"GET /webhook/{FAKE_TOKEN} HTTP/1.1", "n": 1}
        loggers.client.info(
            "request", extra={"first_request_line": f"POST /{FAKE_TOKEN}", "fields": nested}
        )
        record = capture.records[0]
        assert record.msg == "request"
        assert nested["line"].endswith(f"{FAKE_TOKEN} HTTP/1.1")  # caller's dict untouched
        assert record.fields is not nested
        assert record.fields["n"] == 1
        assert_clean(capture)

    def test_stack_info(self):
        stack = "".join(traceback.format_stack()) + f"    fetch('/bot{FAKE_TOKEN}/getMe')"
        record = logging.LogRecord("x", 20, "f", 1, "m", (), None, sinfo=stack)
        loggers.TokenRedactingFilter().filter(record)
        out = logging.Formatter().format(record)
        assert SECRET not in out
        assert MASKED in out

    def test_no_token_leaves_record_untouched(self, capture: _Capture):
        msg, args, extra = "send %s to %d", ("hello", 42), {"payload": {"a": "b"}}
        loggers.client.info(msg, *args, extra=extra)
        record = capture.records[0]
        assert record.msg is msg
        assert record.args == args
        assert record.payload is extra["payload"]

    def test_identity_of_args(self):
        args = ("hello", 42)
        record = logging.LogRecord("x", 20, "f", 1, "send %s to %d", args, None)
        msg = record.msg
        loggers.TokenRedactingFilter().filter(record)
        assert record.msg is msg
        assert record.args is args

    def test_unformattable_record_passes(self):
        record = logging.LogRecord("x", 20, "f", 1, "%s %s", (1, FAKE_TOKEN, "x"), None)
        record.leak = FAKE_TOKEN
        assert loggers.TokenRedactingFilter().filter(record) is True
        # handleError prints the arguments of a record it cannot format
        assert record.args == (1, MASKED, "x")
        assert record.leak == MASKED

    def test_unformattable_record_without_token_keeps_args(self):
        args = (1,)
        record = logging.LogRecord("x", 20, "f", 1, "%s %s", args, None)
        loggers.TokenRedactingFilter().filter(record)
        assert record.args is args

    def test_exc_info_dropped_on_match(self):
        """Formatters that build the traceback from exc_info (JSON loggers) see no token."""
        try:
            raise_chained()
        except RuntimeError:
            record = logging.LogRecord("x", 40, "f", 1, "m", (), sys.exc_info())
        loggers.TokenRedactingFilter().filter(record)
        assert record.exc_info is None
        assert "OSError" in logging.Formatter().format(record)

    def test_exc_info_kept_without_token(self):
        try:
            raise ValueError("plain")
        except ValueError:
            exc_info = sys.exc_info()
        record = logging.LogRecord("x", 40, "f", 1, "m", (), exc_info)
        loggers.TokenRedactingFilter().filter(record)
        assert record.exc_info is exc_info
        assert record.exc_text is None

    def test_long_digit_run_is_linear(self):
        # Without a guard the pattern restarts at every digit: quadratic, seconds for this size
        record = logging.LogRecord("x", 20, "f", 1, "1" * 30_000, (), None)
        started = time.perf_counter()
        loggers.TokenRedactingFilter().filter(record)
        assert time.perf_counter() - started < 0.2

    def test_token_after_digits_keeps_full_id(self):
        record = logging.LogRecord("x", 20, "f", 1, f"/bot{FAKE_TOKEN}/", (), None)
        loggers.TokenRedactingFilter().filter(record)
        assert record.msg == f"/bot{MASKED}/"

    def test_exc_info_without_exception(self):
        record = logging.LogRecord("x", 40, "f", 1, "m", (), (None, None, None))
        assert loggers.TokenRedactingFilter().filter(record) is True
        assert record.exc_text is None

    def test_opt_out(self, capture: _Capture):
        loggers.redact_tokens(False)
        loggers.client.info("a %s", FAKE_TOKEN)
        logging.getLogger("aiogram.client.x").info("b %s", FAKE_TOKEN)
        assert all(SECRET in text for text in capture.text)
        loggers.redact_tokens(True)
        loggers.client.info("c %s", FAKE_TOKEN)
        assert SECRET not in capture.text[-1]

    def test_internal_failure_passes_and_warns_once(self, monkeypatch: pytest.MonkeyPatch):
        class Broken:
            def subn(self, *args: object) -> None:
                raise RuntimeError("broken pattern")

        monkeypatch.setattr(loggers, "_TOKEN_PATTERN", Broken())
        record = logging.LogRecord("x", 20, "f", 1, "m %s", (FAKE_TOKEN,), None)
        with pytest.warns(RuntimeWarning, match="token redaction failed") as warned:
            assert loggers.TokenRedactingFilter().filter(record) is True
            assert loggers.TokenRedactingFilter().filter(record) is True
        assert len(warned) == 1
        assert record.args == (FAKE_TOKEN,)

    def test_warning_as_error_does_not_raise(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(loggers, "_redact_record", lambda record: 1 / 0)
        record = logging.LogRecord("x", 20, "f", 1, "m", (), None)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert loggers.TokenRedactingFilter().filter(record) is True


class TestFactory:
    def test_new_logger_gets_filter(self):
        logger = loggers.get_logger("aiogram.client.created_late")
        assert logger.filters == [loggers._CONTEXT_FILTER, loggers._REDACTING_FILTER]


# Imports every aiogram module, then lists framework loggers that lack the filter. A fresh
# process: this test session holds loggers other tests made with plain logging.getLogger().
WALK = """
import importlib, logging, pkgutil, sys
import aiogram
from aiogram import loggers
{extra}
for info in pkgutil.walk_packages(aiogram.__path__, "aiogram."):
    if info.name != "aiogram.__main__":  # runs the CLI
        importlib.import_module(info.name)
checked = [
    name
    for name, logger in logging.Logger.manager.loggerDict.items()
    if name.startswith("aiogram.") and isinstance(logger, logging.Logger)
]
missing = [n for n in checked if loggers._REDACTING_FILTER not in logging.getLogger(n).filters]
print(len(checked), missing)
sys.exit(1 if missing or not checked else 0)
"""


@pytest.mark.parametrize(
    ("extra", "code"),
    [("", 0), ("logging.getLogger('aiogram.rogue')", 1)],
    ids=["all-filtered", "negative"],
)
def test_logger_dict_walk(extra: str, code: int):
    result = subprocess.run(
        [sys.executable, "-c", WALK.format(extra=extra)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == code, result.stdout + result.stderr
    if code:
        assert "aiogram.rogue" in result.stdout
