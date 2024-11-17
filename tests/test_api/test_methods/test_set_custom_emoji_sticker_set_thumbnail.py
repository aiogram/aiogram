from aiogram.methods import SetCustomEmojiStickerSetThumbnail
from tests.mocked_bot import MockedBot


class TestSetCustomEmojiStickerSetThumbnail:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SetCustomEmojiStickerSetThumbnail, ok=True, result=True
        )

        response: bool = await bot.set_custom_emoji_sticker_set_thumbnail(
            name="test", custom_emoji_id="custom id"
        )
        request = bot.get_request()
        assert response == prepare_result.result
