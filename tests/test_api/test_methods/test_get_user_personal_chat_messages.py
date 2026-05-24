import datetime

from aiogram.methods import GetUserPersonalChatMessages
from aiogram.types import Chat, Message, User
from tests.mocked_bot import MockedBot


class TestGetUserPersonalChatMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetUserPersonalChatMessages,
            ok=True,
            result=[
                Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                    text="test",
                )
            ],
        )

        response = await bot.get_user_personal_chat_messages(user_id=42, limit=10)
        bot.get_request()
        assert response == prepare_result.result
