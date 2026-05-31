from aiogram.methods import GetManagedBotToken
from tests.mocked_bot import MockedBot


class TestGetManagedBotToken:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetManagedBotToken, ok=True, result="42:NEW_TOKEN")

        response: str = await bot.get_managed_bot_token(user_id=42)
        bot.get_request()
        assert response == prepare_result.result
