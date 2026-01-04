from aiogram.methods import AnswerShippingQuery
from tests.mocked_bot import MockedBot


class TestAnswerShippingQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerShippingQuery, ok=True, result=True)

        response: bool = await bot.answer_shipping_query(shipping_query_id="query id", ok=True)
        bot.get_request()
        assert response == prepare_result.result
