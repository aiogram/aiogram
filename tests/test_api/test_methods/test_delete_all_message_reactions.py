from aiogram.methods import DeleteAllMessageReactions
from tests.mocked_bot import MockedBot


class TestDeleteAllMessageReactions:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteAllMessageReactions, ok=True, result=True)

        response: bool = await bot.delete_all_message_reactions(chat_id=42)
        bot.get_request()
        assert response == prepare_result.result
