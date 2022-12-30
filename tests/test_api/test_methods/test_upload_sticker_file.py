from aiogram.methods import Request, UploadStickerFile
from aiogram.types import BufferedInputFile, File
from tests.mocked_bot import MockedBot


class TestUploadStickerFile:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            UploadStickerFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )

        response: File = await UploadStickerFile(
            user_id=42, png_sticker=BufferedInputFile(b"", "file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "uploadStickerFile"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            UploadStickerFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )

        response: File = await bot.upload_sticker_file(
            user_id=42, png_sticker=BufferedInputFile(b"", "file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "uploadStickerFile"
        assert response == prepare_result.result
