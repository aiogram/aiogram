import asyncio
import datetime
from functools import wraps
from typing import Any

import pytest

from aiogram import Bot
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.handlers import BaseHandler
from aiogram.types import Chat, Message, Update


class MyHandler(BaseHandler):
    async def handle(self) -> Any:
        await asyncio.sleep(0.1)
        return 42


class TestBaseClassBasedHandler:
    async def test_base_handler(self):
        event = Update(update_id=42)
        handler = MyHandler(event=event, key=42)

        assert handler.event == event
        assert handler.data["key"] == 42
        assert not hasattr(handler, "filters")
        assert await handler == 42

    async def test_bot_from_context(self):
        event = Update(update_id=42)
        bot = Bot("42:TEST")
        handler = MyHandler(event=event, key=42, bot=bot)
        assert handler.bot == bot

    async def test_bot_from_context_missing(self):
        event = Update(update_id=42)
        handler = MyHandler(event=event, key=42)

        with pytest.raises(RuntimeError):
            handler.bot

    async def test_bot_from_data(self):
        event = Update(update_id=42)
        bot = Bot("42:TEST")
        handler = MyHandler(event=event, key=42, bot=bot)

        assert "bot" in handler.data
        assert handler.bot == bot

    def test_update_from_data(self):
        event = Message(
            message_id=42, chat=Chat(id=42, type="private"), date=datetime.datetime.now()
        )
        update = Update(update_id=42, message=event)
        handler = MyHandler(event=event, update=update)

        assert handler.event == event
        assert handler.update == update

    async def test_wrapped_handler(self):
        # wrap the handler on dummy function
        handler = wraps(MyHandler)(lambda: None)
        assert HandlerObject(handler).awaitable is True
