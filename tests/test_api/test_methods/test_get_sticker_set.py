from aiogram.methods import GetStickerSet
from aiogram.types import Sticker, StickerSet
from tests.mocked_bot import MockedBot


class TestGetStickerSet:
    def test_sticker_set_deserializes_without_deprecated_format_flags(self):
        sticker_set = StickerSet.model_validate(
            {
                "name": "test",
                "title": "test",
                "sticker_type": "regular",
                "stickers": [],
            }
        )

        assert sticker_set.is_animated is None
        assert sticker_set.is_video is None

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetStickerSet,
            ok=True,
            result=StickerSet(
                name="test",
                title="test",
                is_animated=False,
                is_video=False,
                stickers=[
                    Sticker(
                        file_id="file if",
                        width=42,
                        height=42,
                        is_animated=False,
                        is_video=False,
                        file_unique_id="file id",
                        type="regular",
                    )
                ],
                sticker_type="regular",
            ),
        )

        response: StickerSet = await bot.get_sticker_set(name="test")
        bot.get_request()
        assert response == prepare_result.result
