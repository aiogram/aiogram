import pytest
from aiogram.api.methods import AddStickerToSet, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestAddStickerToSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AddStickerToSet, ok=True, result=None)

        response: bool = await AddStickerToSet(
            user_id=..., name=..., png_sticker=..., emojis=...,
        )
        request: Request = bot.get_request()
        assert request.method == "addStickerToSet"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(AddStickerToSet, ok=True, result=None)

        response: bool = await bot.add_sticker_to_set(
            user_id=..., name=..., png_sticker=..., emojis=...,
        )
        request: Request = bot.get_request()
        assert request.method == "addStickerToSet"
        # assert request.data == {}
        assert response == prepare_result.result
