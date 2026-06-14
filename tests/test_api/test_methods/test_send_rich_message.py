import datetime

from aiogram.methods import SendRichMessage
from aiogram.types import Chat, InputRichMessage, Message, RichBlockParagraph, RichMessage, User
from tests.mocked_bot import MockedBot


class TestSendRichMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendRichMessage,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                rich_message=RichMessage(
                    blocks=[RichBlockParagraph(text="Hello")],
                ),
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            ),
        )

        response: Message = await bot.send_rich_message(
            chat_id=42,
            rich_message=InputRichMessage(html="<p>Hello</p>"),
        )
        bot.get_request()
        assert response == prepare_result.result
