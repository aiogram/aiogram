from aiogram.methods import ReopenGeneralForumTopic
from tests.mocked_bot import MockedBot


class TestReopenGeneralForumTopic:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReopenGeneralForumTopic, ok=True, result=True)

        response: bool = await bot.reopen_general_forum_topic(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
