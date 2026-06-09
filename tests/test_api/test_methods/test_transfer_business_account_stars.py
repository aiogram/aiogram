from aiogram.methods import TransferBusinessAccountStars
from tests.mocked_bot import MockedBot


class TestTransferBusinessAccountStars:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(TransferBusinessAccountStars, ok=True, result=True)

        response: bool = await bot.transfer_business_account_stars(
            business_connection_id="test_connection_id", star_count=100
        )
        bot.get_request()
        assert response == prepare_result.result
