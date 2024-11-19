from aiogram.methods import SetStickerSetTitle
from tests.mocked_bot import MockedBot


class TestSetStickerSetTitle:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetTitle, ok=True, result=True)

        response: bool = await bot.set_sticker_set_title(name="test", title="Test")
        request = bot.get_request()
        assert response == prepare_result.result
