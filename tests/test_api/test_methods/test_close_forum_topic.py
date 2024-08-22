from aiogram.methods import CloseForumTopic
from tests.mocked_bot import MockedBot


class TestCloseForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CloseForumTopic, ok=True, result=True)

        response: bool = await bot.close_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
