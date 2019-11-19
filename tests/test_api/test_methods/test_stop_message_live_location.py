import pytest

from aiogram.api.methods import Request, StopMessageLiveLocation
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestStopMessageLiveLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopMessageLiveLocation, ok=True, result=None)

        response: Union[Message, bool] = await StopMessageLiveLocation()
        request: Request = bot.get_request()
        assert request.method == "stopMessageLiveLocation"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopMessageLiveLocation, ok=True, result=None)

        response: Union[Message, bool] = await bot.stop_message_live_location()
        request: Request = bot.get_request()
        assert request.method == "stopMessageLiveLocation"
        # assert request.data == {}
        assert response == prepare_result.result
