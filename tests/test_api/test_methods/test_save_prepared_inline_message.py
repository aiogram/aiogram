from datetime import datetime, timedelta

from aiogram.methods import SavePreparedInlineMessage
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    PreparedInlineMessage,
)
from tests.mocked_bot import MockedBot


class TestSavePreparedInlineMessage:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SavePreparedInlineMessage,
            ok=True,
            result=PreparedInlineMessage(
                id="id",
                expiration_date=datetime.now() + timedelta(days=1),
            ),
        )

        response: PreparedInlineMessage = await bot.save_prepared_inline_message(
            user_id=42,
            result=InlineQueryResultArticle(
                id="id",
                title="title",
                input_message_content=InputTextMessageContent(
                    message_text="message_text",
                ),
            ),
        )
        request = bot.get_request()
        assert response == prepare_result.result
