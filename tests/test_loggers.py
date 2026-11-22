import ast
import asyncio
import datetime
import logging
import threading
from pathlib import Path

import pytest

from aiogram import loggers
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot

KEYS = (
    "aiogram_bot_id",
    "aiogram_update_id",
    "aiogram_update_type",
    "aiogram_router",
    "aiogram_handler",
    "aiogram_phase",
)
MODULE_LOGGERS = (
    "dispatcher",
    "runner",
    "polling",
    "webhook",
    "client",
    "fsm",
    "scene",
    "i18n",
    "event",
    "middlewares",
)
AIOGRAM = Path(loggers.__file__).parent


def make_update(update_id: int) -> Update:
    return Update(
        update_id=update_id,
        message=Message(
            message_id=1,
            date=datetime.datetime.now(),
            text="test",
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
        ),
    )


def context_of(record: logging.LogRecord) -> dict[str, object]:
    return {key: getattr(record, key) for key in KEYS}


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)  # Handler.handle() already holds self.lock


@pytest.fixture
def capture():
    """Capture handler on a framework logger and a user logger; restores levels afterwards."""
    handler = _Capture()
    targets = [loggers.dispatcher, logging.getLogger("tests.user")]
    saved = [(target, target.level) for target in targets]
    for target in targets:
        target.addHandler(handler)
        target.setLevel(logging.DEBUG)
    yield handler
    for target, level in saved:
        target.removeHandler(handler)
        target.setLevel(level)


class TestFactory:
    @pytest.mark.parametrize("name", MODULE_LOGGERS)
    def test_module_logger(self, name: str):
        logger = getattr(loggers, name)
        assert logger.name == f"aiogram.{name}"
        assert loggers._CONTEXT_FILTER in logger.filters

    def test_get_logger_child(self):
        logger = loggers.get_logger("aiogram.client.test_child")
        assert logger is logging.getLogger("aiogram.client.test_child")
        assert loggers._CONTEXT_FILTER in logger.filters

    def test_get_logger_is_idempotent(self):
        loggers.get_logger("aiogram.dispatcher")
        assert loggers.dispatcher.filters.count(loggers._CONTEXT_FILTER) == 1

    def test_reimport_replaces_stale_filter(self):
        stale = loggers._ContextFilter()
        stale.aiogram_framework_filter = True  # a filter left by an earlier import of the module
        user = loggers.context_filter()
        logger = loggers.get_logger("aiogram.client.test_reimport")
        logger.addFilter(stale)
        logger.addFilter(user)
        loggers.get_logger("aiogram.client.test_reimport")
        assert logger.filters == [loggers._CONTEXT_FILTER, loggers._REDACTING_FILTER, user]

    @pytest.mark.parametrize("name", ["aiogram", "aiogramx.foo", "foo.aiogram.bar", ""])
    def test_get_logger_rejects_foreign_names(self, name: str):
        with pytest.raises(ValueError, match="start with 'aiogram.'"):
            loggers.get_logger(name)


class TestRecordContext:
    def test_outside_update_all_none(self, capture: _Capture):
        assert loggers._log_context() is None
        loggers.dispatcher.info("outside")
        [record] = capture.records
        assert context_of(record) == dict.fromkeys(KEYS)
        # format strings that name the keys never raise
        logging.Formatter("%(aiogram_update_id)s %(aiogram_phase)s").format(record)

    def test_explicit_extra_wins(self, capture: _Capture):
        loggers.dispatcher.info("extra", extra={"aiogram_update_id": "mine"})
        [record] = capture.records
        assert record.aiogram_update_id == "mine"
        assert record.aiogram_bot_id is None

    def test_context_filter_on_user_logger(self, capture: _Capture):
        filter_ = loggers.context_filter()
        assert isinstance(filter_, logging.Filter)
        record = logging.LogRecord("tests.user", logging.INFO, __file__, 1, "x", None, None)
        assert filter_.filter(record) is True
        assert context_of(record) == dict.fromkeys(KEYS)

    def test_attributes_written_by_executor(self, capture: _Capture):
        token = loggers._current.set(loggers.LogContext(1, 2, "message"))
        try:
            ctx = loggers._log_context()
            assert ctx is not None
            ctx.router = "main"
            ctx.handler = "handle"
            ctx.phase = "handler"
            loggers.dispatcher.info("stage")
        finally:
            loggers._current.reset(token)
        [record] = capture.records
        assert context_of(record) == {
            "aiogram_bot_id": 1,
            "aiogram_update_id": 2,
            "aiogram_update_type": "message",
            "aiogram_router": "main",
            "aiogram_handler": "handle",
            "aiogram_phase": "handler",
        }


class TestFeedUpdateContext:
    async def test_inside_feed_update(
        self, dispatcher: Dispatcher, bot: MockedBot, capture: _Capture, caplog
    ):
        caplog.set_level(logging.INFO, logger="aiogram.event")

        @dispatcher.message()
        async def handler(message: Message):
            loggers.dispatcher.info("inside")

        await dispatcher.feed_update(bot, make_update(42))

        [record] = capture.records
        assert record.aiogram_bot_id == bot.id
        assert record.aiogram_update_id == 42
        assert record.aiogram_update_type == "message"
        assert (record.aiogram_router, record.aiogram_handler, record.aiogram_phase) == (
            None,
            None,
            None,
        )
        # the final "handled" record of feed_update carries the context too
        [done] = [r for r in caplog.records if r.name == "aiogram.event"]
        assert done.getMessage().startswith("Update id=42 is handled")
        assert done.aiogram_update_id == 42
        assert loggers._log_context() is None

    async def test_unknown_update_type(self, dispatcher: Dispatcher, bot: MockedBot, caplog):
        caplog.set_level(logging.INFO, logger="aiogram.event")
        with pytest.warns(RuntimeWarning, match="unknown update type"):
            await dispatcher.feed_update(bot, Update(update_id=7))
        [done] = [r for r in caplog.records if r.getMessage().startswith("Update id=7")]
        assert done.aiogram_update_id == 7
        assert done.aiogram_update_type is None

    async def test_concurrent_updates_do_not_bleed(
        self, dispatcher: Dispatcher, bot: MockedBot, capture: _Capture
    ):
        @dispatcher.message()
        async def handler(message: Message, event_update: Update):
            await asyncio.sleep(0)
            loggers.dispatcher.info("inside %d", event_update.update_id)
            await asyncio.sleep(0)
            loggers.dispatcher.info("inside %d", event_update.update_id)

        ids = range(1000, 1100)
        await asyncio.gather(*(dispatcher.feed_update(bot, make_update(i)) for i in ids))

        assert len(capture.records) == 200
        for record in capture.records:
            assert record.aiogram_update_id == record.args[0]
        assert {r.aiogram_update_id for r in capture.records} == set(ids)

    async def test_sync_handler_user_logger(
        self, dispatcher: Dispatcher, bot: MockedBot, capture: _Capture
    ):
        user_logger = logging.getLogger("tests.user")
        user_filter = loggers.context_filter()
        user_logger.addFilter(user_filter)
        threads = []

        @dispatcher.message()
        def handler(message: Message):
            threads.append(threading.current_thread())
            user_logger.info("sync")

        try:
            await dispatcher.feed_update(bot, make_update(5))
        finally:
            user_logger.removeFilter(user_filter)

        assert threads[0] is not threading.main_thread()
        [record] = [r for r in capture.records if r.name == "tests.user"]
        assert record.aiogram_update_id == 5
        assert record.aiogram_bot_id == bot.id

    async def test_nested_feed_update_restores_outer(
        self, dispatcher: Dispatcher, bot: MockedBot, capture: _Capture
    ):
        @dispatcher.message()
        async def handler(message: Message, event_update: Update):
            if event_update.update_id == 1:
                await dispatcher.feed_update(bot, make_update(2))
            loggers.dispatcher.info("after %d", event_update.update_id)

        await dispatcher.feed_update(bot, make_update(1))

        assert [(r.args[0], r.aiogram_update_id) for r in capture.records] == [(2, 2), (1, 1)]
        assert loggers._log_context() is None

    async def test_reset_on_error(self, dispatcher: Dispatcher, bot: MockedBot):
        @dispatcher.message()
        async def handler(message: Message):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await dispatcher.feed_update(bot, make_update(3))
        assert loggers._log_context() is None


def _get_logger_calls(tree: ast.AST) -> list[int]:
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name == "getLogger":
            lines.append(node.lineno)
    return lines


def test_guard_no_get_logger_outside_loggers_module():
    offenders = []
    for path in sorted(AIOGRAM.rglob("*.py")):
        if path == AIOGRAM / "loggers.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders += [f"{path.relative_to(AIOGRAM)}:{line}" for line in _get_logger_calls(tree)]
    assert offenders == [], "create framework loggers with aiogram.loggers.get_logger()"


@pytest.mark.parametrize(
    "source",
    [
        "import logging\nlogging.getLogger('aiogram.x')",
        "from logging import getLogger\ngetLogger('aiogram.x')",
    ],
)
def test_guard_detects(source: str):
    assert _get_logger_calls(ast.parse(source)) == [2]


class TestErrorRecordsContext:
    """Records logged around feed_update by the polling and webhook entry points carry the context."""

    @staticmethod
    def failing(dispatcher: Dispatcher) -> None:
        @dispatcher.message()
        async def handler(message: Message):
            raise RuntimeError("boom")

    @staticmethod
    def error_record(caplog) -> logging.LogRecord:
        [record] = [r for r in caplog.records if r.getMessage().startswith("Cause exception")]
        return record

    async def test_process_update(self, dispatcher: Dispatcher, bot: MockedBot, caplog):
        self.failing(dispatcher)
        assert await dispatcher._process_update(bot, make_update(11)) is True
        record = self.error_record(caplog)
        assert (record.aiogram_bot_id, record.aiogram_update_id) == (bot.id, 11)
        assert record.aiogram_update_type == "message"
        assert loggers._log_context() is None

    async def test_feed_webhook_update(self, dispatcher: Dispatcher, bot: MockedBot, caplog):
        self.failing(dispatcher)
        with pytest.raises(RuntimeError):
            await dispatcher._feed_webhook_update(bot, make_update(12))
        assert self.error_record(caplog).aiogram_update_id == 12
        assert loggers._log_context() is None

    async def test_silent_call_request(self, dispatcher: Dispatcher, bot: MockedBot, caplog):
        @dispatcher.message()
        async def handler(message: Message):
            return SendMessage(chat_id=1, text="x")

        bot.add_result_for(SendMessage, ok=False, error_code=400, description="Bad Request")
        await dispatcher._process_update(bot, make_update(13))
        [record] = [
            r for r in caplog.records if r.getMessage().startswith("Failed to make answer")
        ]
        assert record.aiogram_update_id == 13

    async def test_skipped_invalid_update(self, dispatcher: Dispatcher, bot: MockedBot, caplog):
        caplog.set_level(logging.DEBUG, logger="aiogram.webhook")
        await dispatcher.feed_raw_update(bot, {"update_id": 14, "message": {"bad": 1}})
        records = [r for r in caplog.records if r.name == "aiogram.webhook"]
        assert len(records) == 2
        for record in records:
            assert (record.aiogram_bot_id, record.aiogram_update_id) == (bot.id, 14)
            assert record.aiogram_update_type is None
        assert loggers._log_context() is None
