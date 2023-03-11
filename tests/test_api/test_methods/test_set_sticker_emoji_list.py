from aiogram.methods import Request, SetStickerEmojiList
from tests.mocked_bot import MockedBot


class TestSetStickerEmojiList:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerEmojiList, ok=True, result=True)

        response: bool = await SetStickerEmojiList(sticker="sticker id", emoji_list=["X"])
        request: Request = bot.get_request()
        assert request.method == "setStickerEmojiList"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerEmojiList, ok=True, result=True)

        response: bool = await bot.set_sticker_emoji_list(sticker="sticker id", emoji_list=["X"])
        request: Request = bot.get_request()
        assert request.method == "setStickerEmojiList"
        assert response == prepare_result.result
