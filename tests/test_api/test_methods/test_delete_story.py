from aiogram.methods import DeleteStory
from tests.mocked_bot import MockedBot


class TestDeleteStory:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStory, ok=True, result=True)

        response: bool = await bot.delete_story(
            business_connection_id="test_connection_id", story_id=42
        )
        request = bot.get_request()
        assert response == prepare_result.result
