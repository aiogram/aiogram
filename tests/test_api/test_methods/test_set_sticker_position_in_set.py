import pytest

from aiogram.methods import Request, SetStickerPositionInSet
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSetStickerPositionInSet:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerPositionInSet, ok=True, result=True)

        response: bool = await SetStickerPositionInSet(sticker="sticker", position=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerPositionInSet"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerPositionInSet, ok=True, result=True)

        response: bool = await bot.set_sticker_position_in_set(sticker="sticker", position=42)
        request: Request = bot.get_request()
        assert request.method == "setStickerPositionInSet"
        assert response == prepare_result.result
