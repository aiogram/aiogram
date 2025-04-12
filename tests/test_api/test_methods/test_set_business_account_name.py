from aiogram.methods import SetBusinessAccountName
from tests.mocked_bot import MockedBot


class TestSetBusinessAccountName:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetBusinessAccountName, ok=True, result=True)

        response: bool = await bot.set_business_account_name(
            business_connection_id="test_connection_id",
            first_name="Test Business",
            last_name="Account Name",
        )
        request = bot.get_request()
        assert response == prepare_result.result
