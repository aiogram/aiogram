from aiogram.methods import Request, UnpinAllForumTopicMessages
from tests.mocked_bot import MockedBot


class TestUnpinAllForumTopicMessages:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllForumTopicMessages, ok=True, result=True)

        response: bool = await UnpinAllForumTopicMessages(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "unpinAllForumTopicMessages"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnpinAllForumTopicMessages, ok=True, result=True)

        response: bool = await bot.unpin_all_forum_topic_messages(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "unpinAllForumTopicMessages"
        # assert request.data == {}
        assert response == prepare_result.result
