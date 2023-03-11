from aiogram import Bot
from aiogram.methods import AnswerInlineQuery, Request
from aiogram.types import (
    InlineQueryResult,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
from tests.mocked_bot import MockedBot


class TestAnswerInlineQuery:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await bot.answer_inline_query(
            inline_query_id="query id", results=[InlineQueryResult()]
        )
        request = bot.get_request()
        assert response == prepare_result.result
