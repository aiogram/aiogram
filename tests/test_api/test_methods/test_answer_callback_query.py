from aiogram.methods import AnswerCallbackQuery
from tests.mocked_bot import MockedBot


class TestAnswerCallbackQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerCallbackQuery, ok=True, result=True)

        response: bool = await bot.answer_callback_query(callback_query_id="cq id", text="OK")
        request = bot.get_request()
        assert response == prepare_result.result
