from aiogram.methods import Request, SetStickerKeywords
from tests.mocked_bot import MockedBot


class TestSetStickerKeywords:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerKeywords, ok=True, result=True)

        response: bool = await SetStickerKeywords(sticker="sticker id", keywords=["X"])
        request: Request = bot.get_request()
        assert request.method == "setStickerKeywords"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerKeywords, ok=True, result=True)

        response: bool = await bot.set_sticker_keywords(sticker="sticker id", keywords=["X"])
        request: Request = bot.get_request()
        assert request.method == "setStickerKeywords"
        assert response == prepare_result.result
