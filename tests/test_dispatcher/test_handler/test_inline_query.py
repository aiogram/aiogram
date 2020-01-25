from typing import Any

import pytest

from aiogram.api.types import CallbackQuery, InlineQuery, User
from aiogram.dispatcher.handler import InlineQueryHandler


class TestCallbackQueryHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = InlineQuery(
            id="query",
            from_user=User(id=42, is_bot=False, first_name="Test"),
            query="query",
            offset="0",
        )

        class MyHandler(InlineQueryHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user
                assert self.query == self.event.query
                return True

        assert await MyHandler(event)
