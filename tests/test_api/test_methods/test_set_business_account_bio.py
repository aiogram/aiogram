from aiogram.methods import SetBusinessAccountBio
from tests.mocked_bot import MockedBot


class TestSetBusinessAccountBio:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetBusinessAccountBio, ok=True, result=True)

        response: bool = await bot.set_business_account_bio(
            business_connection_id="test_connection_id",
            bio="This is a test bio for the business account",
        )
        bot.get_request()
        assert response == prepare_result.result
