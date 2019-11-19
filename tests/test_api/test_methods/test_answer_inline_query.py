import pytest

from aiogram.api.methods import AnswerInlineQuery, Request
from aiogram.api.types import InlineQueryResult
from tests.mocked_bot import MockedBot


class TestAnswerInlineQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await AnswerInlineQuery(
            inline_query_id="query id", results=[InlineQueryResult()]
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await bot.answer_inline_query(
            inline_query_id="query id", results=[InlineQueryResult()]
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        assert response == prepare_result.result
