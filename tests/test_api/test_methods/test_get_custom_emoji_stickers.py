from typing import List

import pytest

from aiogram.methods import GetCustomEmojiStickers, Request
from aiogram.types import Sticker
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetCustomEmojiStickers:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetCustomEmojiStickers, ok=True, result=None)

        response: List[Sticker] = await GetCustomEmojiStickers(
            custom_emoji_ids=...,
        )
        request: Request = bot.get_request()
        assert request.method == "getCustomEmojiStickers"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetCustomEmojiStickers, ok=True, result=None)

        response: List[Sticker] = await bot.get_custom_emoji_stickers(
            custom_emoji_ids=...,
        )
        request: Request = bot.get_request()
        assert request.method == "getCustomEmojiStickers"
        # assert request.data == {}
        assert response == prepare_result.result
