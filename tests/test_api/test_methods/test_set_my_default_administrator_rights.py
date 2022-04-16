import pytest

from aiogram.api.methods import Request, SetMyDefaultAdministratorRights
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetMyDefaultAdministratorRights:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDefaultAdministratorRights, ok=True, result=None)

        response: bool = await SetMyDefaultAdministratorRights()
        request: Request = bot.get_request()
        assert request.method == "setMyDefaultAdministratorRights"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDefaultAdministratorRights, ok=True, result=None)

        response: bool = await bot.set_my_default_administrator_rights()
        request: Request = bot.get_request()
        assert request.method == "setMyDefaultAdministratorRights"
        # assert request.data == {}
        assert response == prepare_result.result
