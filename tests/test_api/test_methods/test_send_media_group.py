import pytest
from aiogram.api.methods import Request, SendMediaGroup
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendMediaGroup:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendMediaGroup, ok=True, result=None)

        response: List[Message] = await SendMediaGroup(
            chat_id=..., media=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendMediaGroup"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendMediaGroup, ok=True, result=None)

        response: List[Message] = await bot.send_media_group(
            chat_id=..., media=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendMediaGroup"
        # assert request.data == {}
        assert response == prepare_result.result
