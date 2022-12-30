from typing import Any

from aiogram.handlers import PollHandler
from aiogram.types import Poll, PollOption


class TestShippingQueryHandler:
    async def test_attributes_aliases(self):
        event = Poll(
            id="query",
            question="Q?",
            options=[PollOption(text="A1", voter_count=1)],
            is_closed=True,
            is_anonymous=False,
            type="quiz",
            allows_multiple_answers=False,
            total_voter_count=0,
            correct_option_id=0,
        )

        class MyHandler(PollHandler):
            async def handle(self) -> Any:
                assert self.event == event
                assert self.question == self.event.question
                assert self.options == self.event.options

                return True

        assert await MyHandler(event)
