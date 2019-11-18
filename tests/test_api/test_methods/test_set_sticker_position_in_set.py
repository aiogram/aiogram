import pytest
from aiogram.api.methods import Request, SetStickerPositionInSet
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetStickerPositionInSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerPositionInSet, ok=True, result=None)

        response: bool = await SetStickerPositionInSet(
            sticker=..., position=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setStickerPositionInSet"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetStickerPositionInSet, ok=True, result=None)

        response: bool = await bot.set_sticker_position_in_set(
            sticker=..., position=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setStickerPositionInSet"
        # assert request.data == {}
        assert response == prepare_result.result
