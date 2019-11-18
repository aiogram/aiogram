import pytest
from aiogram.api.methods import Request, SendPoll
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendPoll:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendPoll, ok=True, result=None)

        response: Message = await SendPoll(
            chat_id=..., question=..., options=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendPoll"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendPoll, ok=True, result=None)

        response: Message = await bot.send_poll(
            chat_id=..., question=..., options=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendPoll"
        # assert request.data == {}
        assert response == prepare_result.result
