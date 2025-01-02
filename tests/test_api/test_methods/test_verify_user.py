from aiogram.methods import VerifyChat, VerifyUser
from aiogram.types import Poll
from tests.mocked_bot import MockedBot


class TestVerifyUser:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(VerifyUser, ok=True, result=True)

        response: bool = await bot.verify_user(user_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
