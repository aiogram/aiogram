import pytest
from aiogram.api.methods import EditMessageLiveLocation, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestEditMessageLiveLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageLiveLocation, ok=True, result=None)

        response: Union[Message, bool] = await EditMessageLiveLocation(
            latitude=..., longitude=...,
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageLiveLocation"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageLiveLocation, ok=True, result=None)

        response: Union[Message, bool] = await bot.edit_message_live_location(
            latitude=..., longitude=...,
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageLiveLocation"
        # assert request.data == {}
        assert response == prepare_result.result
