from aiogram.enums import StickerFormat
from aiogram.methods import AddStickerToSet, RefundStarPayment
from aiogram.types import InputSticker
from tests.mocked_bot import MockedBot


class TestRefundStarPayment:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(RefundStarPayment, ok=True, result=True)

        response: bool = await bot.refund_star_payment(
            user_id=42,
            telegram_payment_charge_id="12345",
        )
        request = bot.get_request()
        assert response == prepare_result.result
