import asyncio
from typing import Any

import pytest

from aiogram import Bot
from aiogram.api.types import Update
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
        assert hasattr(handler, "bot")
        assert not hasattr(handler, "filters")
        assert await handler == 42

    @pytest.mark.asyncio
    async def test_bot_mixin_from_context(self):
        event = Update(update_id=42)
        handler = MyHandler(event=event, key=42)
        bot = Bot("42:TEST")

        assert handler.bot is None

        Bot.set_current(bot)
        assert handler.bot == bot

    @pytest.mark.asyncio
    async def test_bot_mixin_from_data(self):
        event = Update(update_id=42)
        bot = Bot("42:TEST")
        handler = MyHandler(event=event, key=42, bot=bot)

        assert "bot" in handler.data
        assert handler.bot == bot
