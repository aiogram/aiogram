from aiogram.methods import Request, SetStickerEmojiList, SetStickerMaskPosition
from tests.mocked_bot import MockedBot


class TestSetStickerEmojiList:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerMaskPosition, ok=True, result=True)

        response: bool = await SetStickerMaskPosition(sticker="sticker id")
        request: Request = bot.get_request()
        assert request.method == "setStickerMaskPosition"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerMaskPosition, ok=True, result=True)

        response: bool = await bot.set_sticker_mask_position(sticker="sticker id")
        request: Request = bot.get_request()
        assert request.method == "setStickerMaskPosition"
        assert response == prepare_result.result
