import asyncio
import datetime
from functools import wraps
from typing import Any

import pytest

from aiogram import Bot
from aiogram.api.types import Chat, Message, Update
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.handler.base import BaseHandler


class MyHandler(BaseHandler):
    async def handle(self) -> Any:
        await asyncio.sleep(0.1)
        return 42


class TestBaseClassBasedHandler:
    @pytest.mark.asyncio
    async def test_base_handler(self):
        event = Update(update_id=42)
        handler = MyHandler(event=event, key=42)

        assert handler.event == event
        assert handler.data["key"] == 42
        assert not hasattr(handler, "filters")
        assert await handler == 42

    @pytest.mark.asyncio
    async def test_bot_from_context(self):
        event = Update(update_id=42)
        handler = MyHandler(event=event, key=42)
        bot = Bot("42:TEST")

        with pytest.raises(LookupError):
            handler.bot

        Bot.set_current(bot)
        assert handler.bot == bot

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_wrapped_handler(self):
        # wrap the handler on dummy function
        handler = wraps(MyHandler)(lambda: None)
        assert HandlerObject(handler).awaitable is True
