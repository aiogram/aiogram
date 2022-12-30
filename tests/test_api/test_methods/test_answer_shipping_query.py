from aiogram.methods import AnswerShippingQuery, Request
from tests.mocked_bot import MockedBot


class TestAnswerShippingQuery:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerShippingQuery, ok=True, result=True)

        response: bool = await AnswerShippingQuery(shipping_query_id="query id", ok=True)
        request: Request = bot.get_request()
        assert request.method == "answerShippingQuery"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerShippingQuery, ok=True, result=True)

        response: bool = await bot.answer_shipping_query(shipping_query_id="query id", ok=True)
        request: Request = bot.get_request()
        assert request.method == "answerShippingQuery"
        assert response == prepare_result.result
