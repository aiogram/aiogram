from aiogram.methods import Request, SetStickerSetThumbnail
from tests.mocked_bot import MockedBot


class TestSetStickerSetThumbnail:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetThumbnail, ok=True, result=None)

        response: bool = await SetStickerSetThumbnail(name="test", user_id=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerSetThumbnail"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetThumbnail, ok=True, result=None)

        response: bool = await bot.set_sticker_set_thumbnail(name="test", user_id=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerSetThumbnail"
        # assert request.data == {}
        assert response == prepare_result.result
