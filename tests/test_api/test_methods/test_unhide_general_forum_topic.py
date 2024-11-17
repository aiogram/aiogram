from aiogram.methods import UnhideGeneralForumTopic
from tests.mocked_bot import MockedBot


class TestUnhideGeneralForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UnhideGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.unhide_general_forum_topic(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
