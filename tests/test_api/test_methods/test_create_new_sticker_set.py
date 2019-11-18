import pytest
from aiogram.api.methods import CreateNewStickerSet, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestCreateNewStickerSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=None)

        response: bool = await CreateNewStickerSet(
            user_id=..., name=..., title=..., png_sticker=..., emojis=...,
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=None)

        response: bool = await bot.create_new_sticker_set(
            user_id=..., name=..., title=..., png_sticker=..., emojis=...,
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        # assert request.data == {}
        assert response == prepare_result.result
