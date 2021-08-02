from typing import Union

import pytest

from aiogram.methods import EditMessageReplyMarkup, Request
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestEditMessageReplyMarkup:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageReplyMarkup, ok=True, result=True)

        response: Union[Message, bool] = await EditMessageReplyMarkup(
            chat_id=42,
            inline_message_id="inline message id",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="button", callback_data="placeholder")]
                ]
            ),
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageReplyMarkup"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageReplyMarkup, ok=True, result=True)

        response: Union[Message, bool] = await bot.edit_message_reply_markup(
            chat_id=42,
            inline_message_id="inline message id",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="button", callback_data="placeholder")]
                ]
            ),
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageReplyMarkup"
        assert response == prepare_result.result
