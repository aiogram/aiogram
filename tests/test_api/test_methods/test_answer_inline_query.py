from aiogram import Bot
from aiogram.methods import AnswerInlineQuery, Request
from aiogram.types import (
    InlineQueryResult,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)
from tests.mocked_bot import MockedBot


class TestAnswerInlineQuery:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await AnswerInlineQuery(
            inline_query_id="query id", results=[InlineQueryResult()]
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AnswerInlineQuery, ok=True, result=True)

        response: bool = await bot.answer_inline_query(
            inline_query_id="query id", results=[InlineQueryResult()]
        )
        request: Request = bot.get_request()
        assert request.method == "answerInlineQuery"
        assert response == prepare_result.result

    def test_parse_mode(self, bot: MockedBot):
        query = AnswerInlineQuery(
            inline_query_id="query id",
            results=[
                InlineQueryResultPhoto(id="result id", photo_url="photo", thumbnail_url="thumb")
            ],
        )
        request = query.build_request(bot)
        assert request.data["results"][0]["parse_mode"] is None

        new_bot = Bot(token="42:TEST", parse_mode="HTML")
        request = query.build_request(new_bot)
        assert request.data["results"][0]["parse_mode"] == "HTML"

    def test_parse_mode_input_message_content(self, bot: MockedBot):
        query = AnswerInlineQuery(
            inline_query_id="query id",
            results=[
                InlineQueryResultPhoto(
                    id="result id",
                    photo_url="photo",
                    thumbnail_url="thumb",
                    input_message_content=InputTextMessageContent(message_text="test"),
                )
            ],
        )
        request = query.build_request(bot)
        assert request.data["results"][0]["input_message_content"]["parse_mode"] is None

        new_bot = Bot(token="42:TEST", parse_mode="HTML")
        request = query.build_request(new_bot)
        assert request.data["results"][0]["input_message_content"]["parse_mode"] == "HTML"
