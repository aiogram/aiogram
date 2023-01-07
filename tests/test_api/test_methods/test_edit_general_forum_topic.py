from aiogram.methods import EditGeneralForumTopic, Request
from tests.mocked_bot import MockedBot


class TestCloseGeneralForumTopic:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditGeneralForumTopic, ok=True, result=True)

        response: bool = await bot(EditGeneralForumTopic(chat_id=42, name="Test"))
        request: Request = bot.get_request()
        assert request.method == "editGeneralForumTopic"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.edit_general_forum_topic(chat_id=42, name="Test")
        request: Request = bot.get_request()
        assert request.method == "editGeneralForumTopic"
        assert response == prepare_result.result
