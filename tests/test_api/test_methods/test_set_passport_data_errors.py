import pytest

from aiogram.api.methods import Request, SetPassportDataErrors
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetPassportDataErrors:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetPassportDataErrors, ok=True, result=None)

        response: bool = await SetPassportDataErrors(user_id=..., errors=...)
        request: Request = bot.get_request()
        assert request.method == "setPassportDataErrors"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetPassportDataErrors, ok=True, result=None)

        response: bool = await bot.set_passport_data_errors(user_id=..., errors=...)
        request: Request = bot.get_request()
        assert request.method == "setPassportDataErrors"
        # assert request.data == {}
        assert response == prepare_result.result
