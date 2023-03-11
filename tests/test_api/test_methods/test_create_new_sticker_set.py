from aiogram.enums import StickerFormat
from aiogram.methods import CreateNewStickerSet, Request
from aiogram.types import FSInputFile, InputSticker
from tests.mocked_bot import MockedBot


class TestCreateNewStickerSet:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=True)

        response: bool = await CreateNewStickerSet(
            user_id=42,
            name="name",
            title="title",
            stickers=[
                InputSticker(sticker="file id", emoji_list=[":)"]),
                InputSticker(sticker=FSInputFile("file.png"), emoji_list=["=("]),
            ],
            sticker_format=StickerFormat.STATIC,
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=True)

        response: bool = await bot.create_new_sticker_set(
            user_id=42,
            name="name",
            title="title",
            stickers=[
                InputSticker(sticker="file id", emoji_list=[":)"]),
                InputSticker(sticker=FSInputFile("file.png"), emoji_list=["=("]),
            ],
            sticker_format=StickerFormat.STATIC,
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        assert response == prepare_result.result
