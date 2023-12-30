from random import randint

from aiogram.methods import ForwardMessages
from aiogram.types import MessageId
from tests.mocked_bot import MockedBot


class TestForwardMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ForwardMessages,
            ok=True,
            result=[
                MessageId(message_id=randint(100, 200)),
                MessageId(message_id=randint(200, 300)),
            ],
        )

        response: list[MessageId] = await bot.forward_messages(
            chat_id=randint(10, 50),
            from_chat_id=randint(50, 99),
            message_ids=[
                randint(400, 500),
                randint(600, 700),
            ],
        )
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
