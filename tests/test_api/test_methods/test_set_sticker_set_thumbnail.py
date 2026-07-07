from aiogram.enums import StickerFormat
from aiogram.methods import SetStickerSetThumbnail
from tests.mocked_bot import MockedBot


class TestSetStickerSetThumbnail:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetThumbnail, ok=True, result=None)

        response: bool = await bot.set_sticker_set_thumbnail(
            name="test", format=StickerFormat.STATIC, user_id=42
        )
        bot.get_request()
        assert response == prepare_result.result
