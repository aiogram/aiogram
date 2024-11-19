from aiogram.methods import DeleteStickerFromSet
from tests.mocked_bot import MockedBot


class TestDeleteStickerFromSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteStickerFromSet, ok=True, result=True)

        response: bool = await bot.delete_sticker_from_set(sticker="sticker id")
        request = bot.get_request()
        assert response == prepare_result.result
