import pytest

from aiogram.methods import CreateNewStickerSet, Request
from tests.mocked_bot import MockedBot


class TestCreateNewStickerSet:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=True)

        response: bool = await CreateNewStickerSet(
            user_id=42, name="name", title="title", png_sticker="file id", emojis=":)"
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(CreateNewStickerSet, ok=True, result=True)

        response: bool = await bot.create_new_sticker_set(
            user_id=42, name="name", title="title", png_sticker="file id", emojis=":)"
        )
        request: Request = bot.get_request()
        assert request.method == "createNewStickerSet"
        assert response == prepare_result.result
