from aiogram.methods import UpgradeGift
from tests.mocked_bot import MockedBot


class TestUpgradeGift:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UpgradeGift, ok=True, result=True)

        response: bool = await bot.upgrade_gift(
            business_connection_id="test_connection_id",
            owned_gift_id="test_gift_id",
            keep_original_details=True,
            star_count=100,
        )
        request = bot.get_request()
        assert response == prepare_result.result
