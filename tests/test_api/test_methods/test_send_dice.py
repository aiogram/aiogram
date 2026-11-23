import datetime

from aiogram.methods import SendDice
from aiogram.types import Chat, Dice, Message
from tests.mocked_bot import MockedBot


class TestSendDice:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendDice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                chat=Chat(id=42, type="private"),
                dice=Dice(emoji="🎲", value=6),
            ),
        )

        response: Message = await bot.send_dice(chat_id=42)
        bot.get_request()
        assert response == prepare_result.result
