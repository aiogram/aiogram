from aiogram.methods import DeleteForumTopic
from tests.mocked_bot import MockedBot


class TestDeleteForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteForumTopic, ok=True, result=True)

        response: bool = await bot.delete_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
