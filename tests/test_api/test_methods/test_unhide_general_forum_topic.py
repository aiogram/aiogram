from aiogram.methods import Request, UnhideGeneralForumTopic
from tests.mocked_bot import MockedBot


class TestUnhideGeneralForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnhideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot(UnhideGeneralForumTopic(chat_id=42))
        request: Request = bot.get_request()
        assert request.method == "unhideGeneralForumTopic"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnhideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.unhide_general_forum_topic(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "unhideGeneralForumTopic"
        assert response == prepare_result.result
