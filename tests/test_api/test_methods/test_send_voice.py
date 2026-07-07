import datetime

from aiogram.methods import SendVoice
from aiogram.types import Chat, Message, Voice
from tests.mocked_bot import MockedBot


class TestSendVoice:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendVoice,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                voice=Voice(file_id="file id", duration=0, file_unique_id="file id"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_voice(chat_id=42, voice="file id")
        bot.get_request()
        assert response == prepare_result.result
