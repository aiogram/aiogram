import pytest

from aiogram.api.methods import Request, SendLocation
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendLocation, ok=True, result=None)

        response: Message = await SendLocation(chat_id=..., latitude=..., longitude=...)
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendLocation, ok=True, result=None)

        response: Message = await bot.send_location(chat_id=..., latitude=..., longitude=...)
        request: Request = bot.get_request()
        assert request.method == "sendLocation"
        # assert request.data == {}
        assert response == prepare_result.result
