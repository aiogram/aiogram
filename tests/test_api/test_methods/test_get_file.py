import pytest

from aiogram.methods import GetFile, Request
from aiogram.types import File
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetFile:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )

        response: File = await GetFile(file_id="file id")
        request: Request = bot.get_request()
        assert request.method == "getFile"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetFile, ok=True, result=File(file_id="file id", file_unique_id="file id")
        )

        response: File = await bot.get_file(file_id="file id")
        request: Request = bot.get_request()
        assert request.method == "getFile"
        assert response == prepare_result.result
