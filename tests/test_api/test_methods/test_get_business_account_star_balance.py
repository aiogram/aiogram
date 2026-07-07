from aiogram.methods import GetBusinessAccountStarBalance
from aiogram.types import StarAmount
from tests.mocked_bot import MockedBot


class TestGetBusinessAccountStarBalance:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetBusinessAccountStarBalance,
            ok=True,
            result=StarAmount(
                amount=100,
                nanostar_amount=500000000,
            ),
        )

        response: StarAmount = await bot.get_business_account_star_balance(
            business_connection_id="test_connection_id",
        )
        bot.get_request()
        assert response == prepare_result.result
