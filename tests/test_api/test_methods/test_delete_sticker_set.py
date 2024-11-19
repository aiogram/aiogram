from aiogram.methods import DeleteStickerSet
from tests.mocked_bot import MockedBot


class TestDeleteStickerSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerSet, ok=True, result=True)

        response: bool = await bot.delete_sticker_set(name="test")
        request = bot.get_request()
        assert response == prepare_result.result
