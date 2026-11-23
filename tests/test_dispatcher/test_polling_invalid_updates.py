"""Polling skips an update that can't be validated instead of stalling on its batch."""

import asyncio
import json
import logging
from collections import deque
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.methods import GetUpdates, TelegramMethod
from aiogram.types import Message, Update
from aiogram.types.error_event import ErrorEvent
from tests.mocked_bot import MockedSession, bot_full_info

USER = {"id": 2, "is_bot": False, "first_name": "User"}
CHAT = {"id": 1, "type": "group", "title": "Group"}


def message(update_id: int) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {"message_id": update_id, "date": 1, "chat": CHAT, "text": f"m{update_id}"},
    }


def unknown_status(update_id: int) -> dict[str, Any]:
    """A chat_member update with a ChatMember status this aiogram doesn't know."""
    member = {"status": "member", "user": USER}
    return {
        "update_id": update_id,
        "chat_member": {
            "chat": CHAT,
            "from": USER,
            "date": 1,
            "old_chat_member": member,
            "new_chat_member": {**member, "status": "superadmin"},
        },
    }


def batch(*updates: dict[str, Any]) -> str:
    return json.dumps({"ok": True, "result": list(updates)})


class RawSession(MockedSession):
    """Answers each request with a raw body, so the real check_response decodes it."""

    def __init__(self, *bodies: str) -> None:
        super().__init__()
        self.bodies = deque(bodies)
        self.sent: list[GetUpdates] = []

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: Any = None):
        assert isinstance(method, GetUpdates)
        self.sent.append(method.model_copy())
        if not self.bodies:
            raise asyncio.CancelledError  # ends polling
        response = self.check_response(bot, method, 200, self.bodies.popleft())
        return response.result


def make_bot(*bodies: str) -> tuple[Bot, RawSession]:
    session = RawSession(*bodies)
    bot = Bot("42:TEST", session=session)
    bot._me = bot_full_info(id=42)
    return bot, session


def requested(session: RawSession) -> list[tuple[int | None, int | None]]:
    return [(method.offset, method.limit) for method in session.sent]


async def listen(bot: Bot, **kwargs: Any) -> list[int]:
    received = []
    with pytest.raises(asyncio.CancelledError):
        async for update in Dispatcher._listen_updates(bot, **kwargs):
            assert update.bot is bot
            received.append(update.update_id)
    return received


@pytest.fixture
def asleep():
    with patch("aiogram.utils.backoff.Backoff.asleep", new_callable=AsyncMock) as mocked:
        yield mocked


class TestPollingInvalidUpdates:
    async def test_poison_in_the_middle(self, caplog):
        bot, session = make_bot(batch(message(1), unknown_status(2), message(3)))
        dp = Dispatcher(flag="data")
        handled, reported = [], []

        @dp.message()
        async def on_message(message: Message):
            handled.append(message.message_id)

        @dp.error()
        async def on_error(event: ErrorEvent, flag: str, dispatcher: Dispatcher):
            reported.append((event.update, type(event.exception), flag, dispatcher))

        with caplog.at_level(logging.DEBUG), pytest.raises(asyncio.CancelledError):
            await dp._polling(bot, handle_as_tasks=False)

        assert handled == [1, 3]
        assert reported == [(Update(update_id=2), ValidationError, "data", dp)]
        # Every offset is confirmed, the batch is never fetched again
        assert requested(session) == [(None, None), (4, None)]

        errors = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert [(r.name, r.getMessage()) for r in errors] == [
            (
                "aiogram.dispatcher",
                "Update id=2 is skipped because it can't be validated by bot id=42: "
                "1 validation errors, first: union_tag_invalid "
                "at ('chat_member', 'new_chat_member')",
            ),
        ]
        assert "superadmin" not in errors[0].getMessage()
        [debug] = [r for r in caplog.records if r.getMessage().startswith("Skipped update")]
        assert (debug.name, debug.levelno) == ("aiogram.dispatcher", logging.DEBUG)
        assert "superadmin" in debug.getMessage()

    async def test_failing_error_handler(self, caplog):
        bot, session = make_bot(batch(unknown_status(1), message(2)))
        dp = Dispatcher()
        handled = []

        @dp.message()
        async def on_message(message: Message):
            handled.append(message.message_id)

        @dp.error()
        async def on_error(event: ErrorEvent):
            raise RuntimeError

        with pytest.raises(asyncio.CancelledError):
            await dp._polling(bot, handle_as_tasks=False)

        assert handled == [2]
        assert requested(session) == [(None, None), (3, None)]
        assert "Error handler failed for skipped update id=1 by bot id=42" in caplog.text

    async def test_without_callback(self):
        bot, session = make_bot(batch(unknown_status(1), message(2)), batch(message(3)))

        assert await listen(bot) == [2, 3]
        assert requested(session) == [(None, None), (3, None), (4, None)]

    async def test_without_update_id(self, asleep):
        bot, session = make_bot(
            batch(message(1), {"message": {}}, message(3)),
            # limit=1 response: the same update, now with its id
            batch(unknown_status(2)),
            batch(message(3)),
        )
        on_invalid_update = AsyncMock()

        assert await listen(bot, on_invalid_update=on_invalid_update) == [1, 3]
        on_invalid_update.assert_awaited_once()
        assert on_invalid_update.await_args.args[0] == 2
        # The good prefix is confirmed, then the bad update is fetched alone
        assert requested(session) == [(None, None), (2, 1), (3, None), (4, None)]
        asleep.assert_not_awaited()

    async def test_without_update_id_alone(self, asleep, caplog):
        bot, session = make_bot(
            batch({"message": {}}),
            batch({"message": {}}),
            batch({"message": {}}),
            batch(message(1)),
        )

        with caplog.at_level(logging.INFO):
            assert await listen(bot) == [1]
        # Nothing can be confirmed: limit=1, then back off without advancing
        assert requested(session) == [(None, None), (None, 1), (None, 1), (None, 1), (2, None)]
        assert asleep.await_count == 2
        assert caplog.text.count("Failed to skip an update that can't be validated") == 2
        assert "is skipped" not in caplog.text
        assert caplog.text.count("Connection established") == 1

    @pytest.mark.parametrize(
        "body",
        [
            "<html>Bad Gateway</html>",
            '{"ok": true}',
            '{"ok": true, "result": {"update_id": 1}}',
            '{"result": []}',
            '{"ok": false, "result": [], "error_code": "x"}',
            "[" * 100_000,
        ],
    )
    async def test_unreadable_response(self, asleep, caplog, body):
        bot, session = make_bot(body, body, batch(message(1)))

        assert await listen(bot) == [1]
        # Not a list of updates: back off as for network errors, nothing is isolated
        assert requested(session) == [(None, None), (None, None), (None, None), (2, None)]
        assert asleep.await_count == 2
        assert caplog.text.count("Failed to fetch updates - ClientDecodeError") == 2

    async def test_invalid_envelope_only(self, asleep):
        # Every update is valid, the envelope is not: nothing to skip
        body = '{"ok": true, "result": [], "description": 1}'
        bot, session = make_bot(body, body, batch(message(1)))

        assert await listen(bot) == [1]
        assert requested(session) == [(None, None), (None, 1), (None, 1), (2, None)]
        asleep.assert_awaited_once()

    async def test_network_error_backoff_unchanged(self, asleep):
        bot, session = make_bot(batch(message(1)))
        session.bodies.appendleft('{"ok": false, "error_code": 502, "description": "Bad"}')

        assert await listen(bot) == [1]
        assert requested(session) == [(None, None), (None, None), (2, None)]
        asleep.assert_awaited_once()

    async def test_custom_json_loads(self):
        def loads(content: str) -> Any:
            # A loader that normalises the payload: recovery must decode the same way
            return json.loads(content.replace('"text": "m1"', '"text": "loaded"'))

        bot, session = make_bot(batch(message(1), unknown_status(2)))
        session.json_loads = loads
        texts = []
        with pytest.raises(asyncio.CancelledError):
            async for update in Dispatcher._listen_updates(bot):
                texts.append(update.message.text)
        assert texts == ["loaded"]

    async def test_custom_json_loads_failing(self, asleep):
        def loads(content: str) -> Any:
            raise RuntimeError

        bot, session = make_bot("x", "x")
        session.json_loads = loads

        assert await listen(bot) == []
        assert requested(session) == [(None, None), (None, None), (None, None)]
        assert asleep.await_count == 2
