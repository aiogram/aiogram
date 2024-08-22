from aiogram.methods import SetChatStickerSet
from tests.mocked_bot import MockedBot


class TestSetChatStickerSet:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatStickerSet, ok=True, result=True)

        response: bool = await bot.set_chat_sticker_set(chat_id=-42, sticker_set_name="test")
        request = bot.get_request()
        assert response == prepare_result.result
