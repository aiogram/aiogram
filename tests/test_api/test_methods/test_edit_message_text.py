from aiogram.methods import EditMessageText
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestEditMessageText:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageText, ok=True, result=True)

        response: Message | bool = await bot.edit_message_text(
            chat_id=42, inline_message_id="inline message id", text="text"
        )
        bot.get_request()
        assert response == prepare_result.result
