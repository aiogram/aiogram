import pytest

from aiogram.methods import GetStickerSet, Request
from aiogram.types import Sticker, StickerSet
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetStickerSet:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetStickerSet,
            ok=True,
            result=StickerSet(
                name="test",
                title="test",
                is_animated=False,
                contains_masks=False,
                stickers=[
                    Sticker(
                        file_id="file if",
                        width=42,
                        height=42,
                        is_animated=False,
                        file_unique_id="file id",
                    )
                ],
            ),
        )

        response: StickerSet = await GetStickerSet(name="test")
        request: Request = bot.get_request()
        assert request.method == "getStickerSet"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetStickerSet,
            ok=True,
            result=StickerSet(
                name="test",
                title="test",
                is_animated=False,
                contains_masks=False,
                stickers=[
                    Sticker(
                        file_id="file if",
                        width=42,
                        height=42,
                        is_animated=False,
                        file_unique_id="file id",
                    )
                ],
            ),
        )

        response: StickerSet = await bot.get_sticker_set(name="test")
        request: Request = bot.get_request()
        assert request.method == "getStickerSet"
        assert response == prepare_result.result
