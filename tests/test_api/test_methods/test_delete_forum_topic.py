from aiogram.methods import DeleteForumTopic, Request
from tests.mocked_bot import MockedBot


class TestDeleteForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteForumTopic, ok=True, result=True)

        response: bool = await DeleteForumTopic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "deleteForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteForumTopic, ok=True, result=True)

        response: bool = await bot.delete_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "deleteForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result
