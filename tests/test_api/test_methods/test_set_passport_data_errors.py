import pytest

from aiogram.methods import Request, SetPassportDataErrors
from aiogram.types import PassportElementError
from tests.mocked_bot import MockedBot


class TestSetPassportDataErrors:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetPassportDataErrors, ok=True, result=True)

        response: bool = await SetPassportDataErrors(user_id=42, errors=[PassportElementError()])
        request: Request = bot.get_request()
        assert request.method == "setPassportDataErrors"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetPassportDataErrors, ok=True, result=True)

        response: bool = await bot.set_passport_data_errors(
            user_id=42, errors=[PassportElementError()]
        )
        request: Request = bot.get_request()
        assert request.method == "setPassportDataErrors"
        assert response == prepare_result.result
