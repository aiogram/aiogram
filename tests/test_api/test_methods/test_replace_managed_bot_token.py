from aiogram.methods import ReplaceManagedBotToken
from tests.mocked_bot import MockedBot


class TestReplaceManagedBotToken:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ReplaceManagedBotToken, ok=True, result="42:REPLACED_TOKEN"
        )

        response: str = await bot.replace_managed_bot_token(user_id=42)
        bot.get_request()
        assert response == prepare_result.result
