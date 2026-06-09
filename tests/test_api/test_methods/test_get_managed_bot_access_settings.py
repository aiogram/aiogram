from aiogram.methods import GetManagedBotAccessSettings
from aiogram.types import BotAccessSettings
from tests.mocked_bot import MockedBot


class TestGetManagedBotAccessSettings:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetManagedBotAccessSettings,
            ok=True,
            result=BotAccessSettings(is_access_restricted=False),
        )

        response: BotAccessSettings = await bot.get_managed_bot_access_settings(user_id=42)
        bot.get_request()
        assert response == prepare_result.result
