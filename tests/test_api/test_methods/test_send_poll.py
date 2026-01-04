import datetime

from aiogram.methods import SendPoll
from aiogram.types import Chat, Message, Poll, PollOption
from tests.mocked_bot import MockedBot


class TestSendPoll:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendPoll,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                poll=Poll(
                    id="QA",
                    question="Q",
                    options=[
                        PollOption(text="A", voter_count=0),
                        PollOption(text="B", voter_count=0),
                    ],
                    is_closed=False,
                    is_anonymous=False,
                    type="quiz",
                    allows_multiple_answers=False,
                    total_voter_count=0,
                    correct_option_id=0,
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_poll(
            chat_id=42, question="Q?", options=["A", "B"], correct_option_id=0, type="quiz"
        )
        bot.get_request()
        assert response == prepare_result.result
