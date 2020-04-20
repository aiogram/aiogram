import pytest

from aiogram.api.methods import Request, SetStickerSetThumb
from tests.mocked_bot import MockedBot


class TestSetStickerSetThumb:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetThumb, ok=True, result=None)

        response: bool = await SetStickerSetThumb(name="test", user_id=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerSetThumb"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerSetThumb, ok=True, result=None)

        response: bool = await bot.set_sticker_set_thumb(name="test", user_id=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerSetThumb"
        # assert request.data == {}
        assert response == prepare_result.result
