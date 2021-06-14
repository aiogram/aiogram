import pytest

from aiogram.methods import Request, SetChatPhoto
from aiogram.types import BufferedInputFile
from tests.mocked_bot import MockedBot


class TestSetChatPhoto:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPhoto, ok=True, result=True)

        response: bool = await SetChatPhoto(
            chat_id=-42, photo=BufferedInputFile(b"", filename="file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPhoto"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPhoto, ok=True, result=True)

        response: bool = await bot.set_chat_photo(
            chat_id=-42, photo=BufferedInputFile(b"", filename="file.png")
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPhoto"
        assert response == prepare_result.result
