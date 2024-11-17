from aiogram.methods import SendDice
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestSendDice:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendDice, ok=True, result=None)

        response: Message = await bot.send_dice(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
