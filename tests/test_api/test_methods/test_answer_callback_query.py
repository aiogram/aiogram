import pytest

from aiogram.methods import AnswerCallbackQuery, Request
from tests.mocked_bot import MockedBot


class TestAnswerCallbackQuery:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerCallbackQuery, ok=True, result=True)

        response: bool = await AnswerCallbackQuery(callback_query_id="cq id", text="OK")
        request: Request = bot.get_request()
        assert request.method == "answerCallbackQuery"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerCallbackQuery, ok=True, result=True)

        response: bool = await bot.answer_callback_query(callback_query_id="cq id", text="OK")
        request: Request = bot.get_request()
        assert request.method == "answerCallbackQuery"
        assert response == prepare_result.result
