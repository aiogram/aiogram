from typing import List

from aiogram.methods import GetCustomEmojiStickers, Request
from aiogram.types import Sticker
from tests.mocked_bot import MockedBot


class TestGetCustomEmojiStickers:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetCustomEmojiStickers,
            ok=True,
            result=[
                Sticker(
                    file_id="file id",
                    width=42,
                    height=42,
                    is_animated=False,
                    is_video=False,
                    file_unique_id="file id",
                    custom_emoji_id="1",
                    type="custom_emoji",
                )
            ],
        )

        response: List[Sticker] = await GetCustomEmojiStickers(
            custom_emoji_ids=["1"],
        )
        request: Request = bot.get_request()
        assert request.method == "getCustomEmojiStickers"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetCustomEmojiStickers,
            ok=True,
            result=[
                Sticker(
                    file_id="file id",
                    width=42,
                    height=42,
                    is_animated=False,
                    is_video=False,
                    file_unique_id="file id",
                    custom_emoji_id="1",
                    type="custom_emoji",
                )
            ],
        )

        response: List[Sticker] = await bot.get_custom_emoji_stickers(
            custom_emoji_ids=["1", "2"],
        )
        request: Request = bot.get_request()
        assert request.method == "getCustomEmojiStickers"
        # assert request.data == {}
        assert response == prepare_result.result
