from aiogram.methods import ReopenForumTopic
from tests.mocked_bot import MockedBot


class TestReopenForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReopenForumTopic, ok=True, result=None)

        response: bool = await bot.reopen_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        bot.get_request()
        assert response == prepare_result.result
