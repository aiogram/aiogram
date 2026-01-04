from aiogram.methods import DeleteChatPhoto
from tests.mocked_bot import MockedBot


class TestDeleteChatPhoto:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatPhoto, ok=True, result=True)

        response: bool = await bot.delete_chat_photo(chat_id=42)
        bot.get_request()
        assert response == prepare_result.result
