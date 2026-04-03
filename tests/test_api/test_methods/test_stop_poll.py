from aiogram.methods import StopPoll
from aiogram.types import Poll, PollOption
from tests.mocked_bot import MockedBot


class TestStopPoll:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            StopPoll,
            ok=True,
            result=Poll(
                id="QA",
                question="Q",
                options=[
                    PollOption(persistent_id="1", text="A", voter_count=0),
                    PollOption(persistent_id="2", text="B", voter_count=0),
                ],
                is_closed=False,
                is_anonymous=False,
                type="quiz",
                allows_multiple_answers=False,
                allows_revoting=False,
                total_voter_count=0,
                correct_option_ids=[0],
            ),
        )

        response: Poll = await bot.stop_poll(chat_id=42, message_id=42)
        bot.get_request()
        assert response == prepare_result.result
