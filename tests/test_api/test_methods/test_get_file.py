import pytest
from aiogram.api.methods import GetFile, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetFile:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetFile, ok=True, result=None)

        response: File = await GetFile(file_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getFile"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetFile, ok=True, result=None)

        response: File = await bot.get_file(file_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getFile"
        # assert request.data == {}
        assert response == prepare_result.result
