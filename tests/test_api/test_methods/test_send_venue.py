import pytest

from aiogram.api.methods import Request, SendVenue
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendVenue:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVenue, ok=True, result=None)

        response: Message = await SendVenue(
            chat_id=..., latitude=..., longitude=..., title=..., address=...
        )
        request: Request = bot.get_request()
        assert request.method == "sendVenue"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVenue, ok=True, result=None)

        response: Message = await bot.send_venue(
            chat_id=..., latitude=..., longitude=..., title=..., address=...
        )
        request: Request = bot.get_request()
        assert request.method == "sendVenue"
        # assert request.data == {}
        assert response == prepare_result.result
