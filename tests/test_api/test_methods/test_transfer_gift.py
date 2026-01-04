from aiogram.methods import TransferGift
from tests.mocked_bot import MockedBot


class TestTransferGift:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(TransferGift, ok=True, result=True)

        response: bool = await bot.transfer_gift(
            business_connection_id="test_connection_id",
            owned_gift_id="test_gift_id",
            new_owner_chat_id=123456789,
            star_count=50,
        )
        bot.get_request()
        assert response == prepare_result.result
