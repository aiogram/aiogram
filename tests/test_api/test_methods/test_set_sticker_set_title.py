from aiogram.methods import Request, SetStickerEmojiList, SetStickerSetTitle
from tests.mocked_bot import MockedBot


class TestSetStickerSetTitle:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetTitle, ok=True, result=True)

        response: bool = await SetStickerSetTitle(name="test", title="Test")
        request: Request = bot.get_request()
        assert request.method == "setStickerSetTitle"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetTitle, ok=True, result=True)

        response: bool = await bot.set_sticker_set_title(name="test", title="Test")
        request: Request = bot.get_request()
        assert request.method == "setStickerSetTitle"
        assert response == prepare_result.result
