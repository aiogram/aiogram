from aiogram.methods import ReplaceStickerInSet
from aiogram.types import InputSticker
from tests.mocked_bot import MockedBot


class TestReplaceStickerInSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReplaceStickerInSet, ok=True, result=True)

        response: bool = await bot.replace_sticker_in_set(
            user_id=42,
            name="test",
            old_sticker="test",
            sticker=InputSticker(
                sticker="test",
                format="static",
                emoji_list=["test"],
            ),
        )
        request = bot.get_request()
        assert response == prepare_result.result
