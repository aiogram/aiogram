from aiogram.methods import DeleteBusinessAccountGift
from tests.mocked_bot import MockedBot


class TestDeleteBusinessAccountGift:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteBusinessAccountGift, ok=True, result=True)

        response: bool = await bot.delete_business_account_gift(
            business_connection_id="test_connection_id", owned_gift_id="test_gift_id"
        )
        bot.get_request()
        assert response == prepare_result.result
