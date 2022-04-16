import pytest

from aiogram.methods import GetMyDefaultAdministratorRights, Request
from aiogram.types import ChatAdministratorRights
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetMyDefaultAdministratorRights:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyDefaultAdministratorRights, ok=True, result=None)

        response: ChatAdministratorRights = await GetMyDefaultAdministratorRights()
        request: Request = bot.get_request()
        assert request.method == "getMyDefaultAdministratorRights"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetMyDefaultAdministratorRights, ok=True, result=None)

        response: ChatAdministratorRights = await bot.get_my_default_administrator_rights()
        request: Request = bot.get_request()
        assert request.method == "getMyDefaultAdministratorRights"
        # assert request.data == {}
        assert response == prepare_result.result
