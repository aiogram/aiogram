import pytest
from aiogram.api.methods import Request, StopPoll
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestStopPoll:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopPoll, ok=True, result=None)

        response: Poll = await StopPoll(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "stopPoll"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopPoll, ok=True, result=None)

        response: Poll = await bot.stop_poll(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "stopPoll"
        # assert request.data == {}
        assert response == prepare_result.result
