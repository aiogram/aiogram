import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from aiogram import Bot, flags
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.types import Chat, Message, User
from aiogram.utils.chat_action import ChatActionMiddleware, ChatActionSender
from tests.mocked_bot import MockedBot


class TestChatActionSender:
    async def test_wait(self, bot: Bot, event_loop: asyncio.BaseEventLoop):
        sender = ChatActionSender.typing(bot=bot, chat_id=42)
        event_loop.call_soon(sender._close_event.set)
        start = time.monotonic()
        await sender._wait(1)
        assert time.monotonic() - start < 1

    @pytest.mark.parametrize(
        "action",
        [
            "typing",
            "upload_photo",
            "record_video",
            "upload_video",
            "record_voice",
            "upload_voice",
            "upload_document",
            "choose_sticker",
            "find_location",
            "record_video_note",
            "upload_video_note",
        ],
    )
    async def test_factory(self, action: str, bot: MockedBot):
        sender_factory = getattr(ChatActionSender, action)
        sender = sender_factory(chat_id=42, bot=bot)
        assert isinstance(sender, ChatActionSender)
        assert sender.action == action
        assert sender.chat_id == 42
        assert sender.bot is bot

    async def test_worker(self, bot: Bot):
        with patch(
            "aiogram.client.bot.Bot.send_chat_action",
            new_callable=AsyncMock,
        ) as mocked_send_chat_action:
            async with ChatActionSender.typing(
                bot=bot, chat_id=42, interval=0.01, initial_sleep=0
            ):
                await asyncio.sleep(0.1)
                assert mocked_send_chat_action.await_count > 1
                mocked_send_chat_action.assert_awaited_with(
                    action="typing",
                    chat_id=42,
                    message_thread_id=None,
                )

    async def test_contextmanager(self, bot: MockedBot):
        sender: ChatActionSender = ChatActionSender.typing(bot=bot, chat_id=42)
        assert not sender.running
        await sender._stop()  # nothing

        async with sender:
            assert sender.running
            assert not sender._close_event.is_set()

            with pytest.raises(RuntimeError):
                await sender._run()

        assert not sender.running


class TestChatActionMiddleware:
    @pytest.mark.parametrize(
        "value",
        [
            None,
            "sticker",
            {"action": "upload_photo"},
            {"interval": 1, "initial_sleep": 0.5},
        ],
    )
    async def test_call_default(self, value, bot: Bot):
        async def handler(event, data):
            return "OK"

        if value is None:
            handler1 = flags.chat_action(handler)
        else:
            handler1 = flags.chat_action(value)(handler)

        middleware = ChatActionMiddleware()
        with patch(
            "aiogram.utils.chat_action.ChatActionSender._run",
            new_callable=AsyncMock,
        ) as mocked_run, patch(
            "aiogram.utils.chat_action.ChatActionSender._stop",
            new_callable=AsyncMock,
        ) as mocked_stop:
            data = {"handler": HandlerObject(callback=handler1), "bot": bot}
            message = Message(
                chat=Chat(id=42, type="private", title="Test"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
                date=datetime.now(),
                message_id=42,
            )

            result = await middleware(handler=handler1, event=None, data=data)
            assert result == "OK"
            mocked_run.assert_not_awaited()
            mocked_stop.assert_not_awaited()

            result = await middleware(
                handler=handler1,
                event=message,
                data=data,
            )
            assert result == "OK"
            mocked_run.assert_awaited()
            mocked_stop.assert_awaited()
