import pytest

from aiogram.methods import AnswerWebAppQuery, Request
from aiogram.types import SentWebAppMessage
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestAnswerWebAppQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerWebAppQuery, ok=True, result=None)

        response: SentWebAppMessage = await AnswerWebAppQuery(
            web_app_query_id=...,
            result=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerWebAppQuery"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerWebAppQuery, ok=True, result=None)

        response: SentWebAppMessage = await bot.answer_web_app_query(
            web_app_query_id=...,
            result=...,
        )
        request: Request = bot.get_request()
        assert request.method == "answerWebAppQuery"
        # assert request.data == {}
        assert response == prepare_result.result
