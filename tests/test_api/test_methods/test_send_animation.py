import datetime

from aiogram.methods import SendAnimation
from aiogram.types import Animation, Chat, Message
from tests.mocked_bot import MockedBot


class TestSendAnimation:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendAnimation,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                animation=Animation(
                    file_id="file id", width=42, height=42, duration=0, file_unique_id="file id"
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_animation(chat_id=42, animation="file id")
        bot.get_request()
        assert response == prepare_result.result
