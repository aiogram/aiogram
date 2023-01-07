from aiogram.methods import HideGeneralForumTopic, Request
from tests.mocked_bot import MockedBot


class TestHideGeneralForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(HideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot(HideGeneralForumTopic(chat_id=42))
        request: Request = bot.get_request()
        assert request.method == "hideGeneralForumTopic"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(HideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.hide_general_forum_topic(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "hideGeneralForumTopic"
        assert response == prepare_result.result
