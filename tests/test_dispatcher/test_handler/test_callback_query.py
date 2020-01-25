from typing import Any

import pytest

from aiogram.api.types import CallbackQuery, User
from aiogram.dispatcher.handler import CallbackQueryHandler


class TestCallbackQueryHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = CallbackQuery(
            id="chosen",
            from_user=User(id=42, is_bot=False, first_name="Test"),
            data="test",
            chat_instance="test",
        )

        class MyHandler(CallbackQueryHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user
                assert self.callback_data == self.event.data
                assert self.message == self.message
                return True

        assert await MyHandler(event)
