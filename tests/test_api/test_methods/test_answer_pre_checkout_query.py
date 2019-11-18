import pytest
from aiogram.api.methods import AnswerPreCheckoutQuery, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestAnswerPreCheckoutQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerPreCheckoutQuery, ok=True, result=None)

        response: bool = await AnswerPreCheckoutQuery(
            pre_checkout_query_id=..., ok=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerPreCheckoutQuery"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerPreCheckoutQuery, ok=True, result=None)

        response: bool = await bot.answer_pre_checkout_query(
            pre_checkout_query_id=..., ok=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerPreCheckoutQuery"
        # assert request.data == {}
        assert response == prepare_result.result
