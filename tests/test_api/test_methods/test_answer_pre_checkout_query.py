from aiogram.methods import AnswerPreCheckoutQuery, Request
from tests.mocked_bot import MockedBot


class TestAnswerPreCheckoutQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerPreCheckoutQuery, ok=True, result=True)

        response: bool = await bot.answer_pre_checkout_query(
            pre_checkout_query_id="query id", ok=True
        )
        request = bot.get_request()
        assert response == prepare_result.result
