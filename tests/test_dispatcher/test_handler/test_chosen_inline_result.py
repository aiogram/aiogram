from typing import Any

import pytest

from aiogram.api.types import CallbackQuery, ChosenInlineResult, User
from aiogram.dispatcher.handler import ChosenInlineResultHandler


class TestChosenInlineResultHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = ChosenInlineResult(
            result_id="chosen",
            from_user=User(id=42, is_bot=False, first_name="Test"),
            query="test",
        )

        class MyHandler(ChosenInlineResultHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.from_user == self.event.from_user
                assert self.query == self.event.query
                return True

        assert await MyHandler(event)
