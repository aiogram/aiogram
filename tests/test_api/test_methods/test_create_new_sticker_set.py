from aiogram.enums import StickerFormat
from aiogram.methods import CreateNewStickerSet
from aiogram.types import FSInputFile, InputSticker
from tests.mocked_bot import MockedBot


class TestCreateNewStickerSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=True)

        response: bool = await bot.create_new_sticker_set(
            user_id=42,
            name="name",
            title="title",
            stickers=[
                InputSticker(sticker="file id", format=StickerFormat.STATIC, emoji_list=[":)"]),
                InputSticker(
                    sticker=FSInputFile("file.png"), format=StickerFormat.STATIC, emoji_list=["=("]
                ),
            ],
            sticker_format=StickerFormat.STATIC,
        )
        request = bot.get_request()
        assert response == prepare_result.result
