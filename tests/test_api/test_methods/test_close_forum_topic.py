from aiogram.methods import CloseForumTopic, Request
from tests.mocked_bot import MockedBot


class TestCloseForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CloseForumTopic, ok=True, result=True)

        response: bool = await CloseForumTopic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "closeForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CloseForumTopic, ok=True, result=True)

        response: bool = await bot.close_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "closeForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result
