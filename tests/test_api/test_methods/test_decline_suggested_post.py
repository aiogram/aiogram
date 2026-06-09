from aiogram.methods import DeclineSuggestedPost
from tests.mocked_bot import MockedBot


class TestDeclineSuggestedPost:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeclineSuggestedPost, ok=True, result=True)

        response: bool = await bot.decline_suggested_post(
            chat_id=-42,
            message_id=42,
        )
        bot.get_request()
        assert response == prepare_result.result
