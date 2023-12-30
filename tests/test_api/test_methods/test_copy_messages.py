from random import randint

from aiogram.methods import CopyMessages
from aiogram.types import MessageId
from tests.mocked_bot import MockedBot


class TestCopyMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            CopyMessages,
            ok=True,
            result=[
                MessageId(message_id=randint(100, 200)),
                MessageId(message_id=randint(300, 400)),
            ],
        )

        response: list[MessageId] = await bot.copy_messages(
            chat_id=randint(1000, 9999),
            from_chat_id=randint(1000, 9999),
            message_ids=[
                randint(1000, 4999),
                randint(5000, 9999),
            ],
        )
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
