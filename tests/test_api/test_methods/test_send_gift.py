from aiogram.methods import SendGift
from tests.mocked_bot import MockedBot


class TestSendGift:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendGift, ok=True, result=True)

        response: bool = await bot.send_gift(user_id=42, gift_id="gift_id")
        request = bot.get_request()
        assert response == prepare_result.result
