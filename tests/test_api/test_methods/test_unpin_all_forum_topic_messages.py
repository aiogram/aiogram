from aiogram.methods import UnpinAllForumTopicMessages
from tests.mocked_bot import MockedBot


class TestUnpinAllForumTopicMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllForumTopicMessages, ok=True, result=True)

        response: bool = await bot.unpin_all_forum_topic_messages(
            chat_id=42,
            message_thread_id=42,
        )
        bot.get_request()
        assert response == prepare_result.result
