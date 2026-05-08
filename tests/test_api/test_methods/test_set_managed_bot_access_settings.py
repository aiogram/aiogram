from aiogram.methods import SetManagedBotAccessSettings
from tests.mocked_bot import MockedBot


class TestSetManagedBotAccessSettings:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetManagedBotAccessSettings, ok=True, result=True)

        response: bool = await bot.set_managed_bot_access_settings(
            user_id=42, is_access_restricted=False
        )
        bot.get_request()
        assert response == prepare_result.result
