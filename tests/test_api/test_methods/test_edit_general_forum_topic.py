from aiogram.methods import EditGeneralForumTopic
from tests.mocked_bot import MockedBot


class TestCloseGeneralForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.edit_general_forum_topic(chat_id=42, name="Test")
        request = bot.get_request()
        assert response == prepare_result.result
