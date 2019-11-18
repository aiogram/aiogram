import pytest
from aiogram.api.methods import AnswerInlineQuery, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestAnswerInlineQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=None)

        response: bool = await AnswerInlineQuery(
            inline_query_id=..., results=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=None)

        response: bool = await bot.answer_inline_query(
            inline_query_id=..., results=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        # assert request.data == {}
        assert response == prepare_result.result
