import pytest
from aiogram.api.methods import ForwardMessage, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestForwardMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ForwardMessage, ok=True, result=None)

        response: Message = await ForwardMessage(
            chat_id=..., from_chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "forwardMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ForwardMessage, ok=True, result=None)

        response: Message = await bot.forward_message(
            chat_id=..., from_chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "forwardMessage"
        # assert request.data == {}
        assert response == prepare_result.result
