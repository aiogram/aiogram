import datetime

import pytest

from aiogram.api.methods import Request, SendPoll
from aiogram.api.types import Chat, Message, Poll, PollOption
from tests.conftest import private_chat
from tests.factories.message import MessageFactory
from tests.mocked_bot import MockedBot


class TestSendPoll:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendPoll,
            ok=True,
            result=MessageFactory(
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
                chat=private_chat,
            ),
        )

        response: Message = await SendPoll(
            chat_id=private_chat.id,
            question="Q?",
            options=["A", "B"],
            correct_option_id=0,
            type="quiz",
        )
        request: Request = bot.get_request()
        assert request.method == "sendPoll"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot, private_chat: Chat):
        prepare_result = bot.add_result_for(
            SendPoll,
            ok=True,
            result=MessageFactory(
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
                chat=private_chat,
            ),
        )

        response: Message = await bot.send_poll(
            chat_id=private_chat.id,
            question="Q?",
            options=["A", "B"],
            correct_option_id=0,
            type="quiz",
        )
        request: Request = bot.get_request()
        assert request.method == "sendPoll"
        assert response == prepare_result.result
