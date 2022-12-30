from aiogram.methods import EditForumTopic, Request
from tests.mocked_bot import MockedBot


class TestEditForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditForumTopic, ok=True, result=True)

        response: bool = await EditForumTopic(
            chat_id=42,
            message_thread_id=42,
            name="test",
            icon_color=0xFFD67E,
            icon_custom_emoji_id="0",
        )
        request: Request = bot.get_request()
        assert request.method == "editForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditForumTopic, ok=True, result=True)

        response: bool = await bot.edit_forum_topic(
            chat_id=42,
            message_thread_id=42,
            name="test",
            icon_custom_emoji_id="0",
        )
        request: Request = bot.get_request()
        assert request.method == "editForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result
