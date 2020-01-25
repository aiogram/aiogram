import pytest

from aiogram.api.methods import Request, StopPoll
from aiogram.api.types import Poll, PollOption
from tests.mocked_bot import MockedBot


class TestStopPoll:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            StopPoll,
            ok=True,
            result=Poll(
                id="QA",
                question="Q",
                options=[PollOption(text="A", voter_count=0), PollOption(text="B", voter_count=0)],
                is_closed=False,
                is_anonymous=False,
                type="quiz",
                allows_multiple_answers=False,
                total_voter_count=0,
                correct_option_id=0,
            ),
        )

        response: Poll = await StopPoll(chat_id=42, message_id=42)
        request: Request = bot.get_request()
        assert request.method == "stopPoll"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            StopPoll,
            ok=True,
            result=Poll(
                id="QA",
                question="Q",
                options=[PollOption(text="A", voter_count=0), PollOption(text="B", voter_count=0)],
                is_closed=False,
                is_anonymous=False,
                type="quiz",
                allows_multiple_answers=False,
                total_voter_count=0,
                correct_option_id=0,
            ),
        )

        response: Poll = await bot.stop_poll(chat_id=42, message_id=42)
        request: Request = bot.get_request()
        assert request.method == "stopPoll"
        assert response == prepare_result.result
