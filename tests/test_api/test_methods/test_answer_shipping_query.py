import pytest
from aiogram.api.methods import AnswerShippingQuery, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestAnswerShippingQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerShippingQuery, ok=True, result=None)

        response: bool = await AnswerShippingQuery(
            shipping_query_id=..., ok=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerShippingQuery"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerShippingQuery, ok=True, result=None)

        response: bool = await bot.answer_shipping_query(
            shipping_query_id=..., ok=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerShippingQuery"
        # assert request.data == {}
        assert response == prepare_result.result
