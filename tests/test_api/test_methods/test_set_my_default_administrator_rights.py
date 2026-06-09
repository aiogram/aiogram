from aiogram.methods import SetMyDefaultAdministratorRights
from tests.mocked_bot import MockedBot


class TestSetMyDefaultAdministratorRights:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetMyDefaultAdministratorRights, ok=True, result=True)

        response: bool = await bot.set_my_default_administrator_rights()
        bot.get_request()
        assert response == prepare_result.result
