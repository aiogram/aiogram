from typing import Any

import pytest
from aiogram.api.types import (
    CallbackQuery,
    InlineQuery,
    Poll,
    PollOption,
    ShippingAddress,
    ShippingQuery,
    User,
)
from aiogram.dispatcher.handler import PollHandler


class TestShippingQueryHandler:
    @pytest.mark.asyncio
    async def test_attributes_aliases(self):
        event = Poll(
            id="query",
            question="Q?",
            options=[PollOption(text="A1", voter_count=1)],
            is_closed=True,
        )

        class MyHandler(PollHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.question == self.event.question
                assert self.options == self.event.options

                return True

        assert await MyHandler(event)
