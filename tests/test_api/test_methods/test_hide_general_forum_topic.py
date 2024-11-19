from aiogram.methods import HideGeneralForumTopic
from tests.mocked_bot import MockedBot


class TestHideGeneralForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(HideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.hide_general_forum_topic(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
