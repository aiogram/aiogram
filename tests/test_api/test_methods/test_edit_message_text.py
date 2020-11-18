from typing import Union

import pytest

from aiogram.methods import EditMessageText, Request
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestEditMessageText:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageText, ok=True, result=True)

        response: Union[Message, bool] = await EditMessageText(
            chat_id=42, inline_message_id="inline message id", text="text"
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageText"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageText, ok=True, result=True)

        response: Union[Message, bool] = await bot.edit_message_text(
            chat_id=42, inline_message_id="inline message id", text="text"
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageText"
        assert response == prepare_result.result
