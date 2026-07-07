from aiogram.methods import RemoveUserVerification
from tests.mocked_bot import MockedBot


class TestRemoveUserVerification:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RemoveUserVerification, ok=True, result=True)

        response: bool = await bot.remove_user_verification(user_id=42)
        bot.get_request()
        assert response == prepare_result.result
