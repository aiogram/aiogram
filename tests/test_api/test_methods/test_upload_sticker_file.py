import pytest
from aiogram.api.methods import Request, UploadStickerFile
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestUploadStickerFile:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UploadStickerFile, ok=True, result=None)

        response: File = await UploadStickerFile(
            user_id=..., png_sticker=...,
        )
        request: Request = bot.get_request()
        assert request.method == "uploadStickerFile"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(UploadStickerFile, ok=True, result=None)

        response: File = await bot.upload_sticker_file(
            user_id=..., png_sticker=...,
        )
        request: Request = bot.get_request()
        assert request.method == "uploadStickerFile"
        # assert request.data == {}
        assert response == prepare_result.result
