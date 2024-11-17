import datetime

from aiogram.methods import SendDocument
from aiogram.types import Chat, Document, Message
from tests.mocked_bot import MockedBot


class TestSendDocument:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendDocument,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                document=Document(file_id="file id", file_unique_id="file id"),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_document(chat_id=42, document="file id")
        request = bot.get_request()
        assert response == prepare_result.result
