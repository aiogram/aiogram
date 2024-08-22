from aiogram.methods import DeleteChatStickerSet
from tests.mocked_bot import MockedBot


class TestDeleteChatStickerSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteChatStickerSet, ok=True, result=True)

        response: bool = await bot.delete_chat_sticker_set(chat_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
