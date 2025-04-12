from aiogram.methods import SetBusinessAccountUsername
from tests.mocked_bot import MockedBot


class TestSetBusinessAccountUsername:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetBusinessAccountUsername, ok=True, result=True)

        response: bool = await bot.set_business_account_username(
            business_connection_id="test_connection_id", username="test_business_username"
        )
        request = bot.get_request()
        assert response == prepare_result.result
