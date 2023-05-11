from aiogram.methods import Request, SendDice
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


class TestSendDice:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendDice,
            ok=True,
            result=Message(
                message_id=42,
                date=123,
                text="text",
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_dice(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
