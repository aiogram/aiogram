import datetime

from aiogram.methods import ForwardMessage
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


class TestForwardMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ForwardMessage,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                chat=Chat(id=42, title="chat", type="private"),
                text="text",
            ),
        )

        response: Message = await bot.forward_message(chat_id=42, from_chat_id=42, message_id=42)
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
