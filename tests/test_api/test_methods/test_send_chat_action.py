from aiogram.enums import ChatAction
from aiogram.methods import SendChatAction
from tests.mocked_bot import MockedBot


class TestSendChatAction:
    async def test_chat_action_class(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=True)

        response: bool = await bot.send_chat_action(chat_id=42, action=ChatAction.TYPING)
        bot.get_request()
        assert response == prepare_result.result
