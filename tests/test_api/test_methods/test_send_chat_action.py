import pytest
from aiogram.api.methods import Request, SendChatAction
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendChatAction:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=None)

        response: bool = await SendChatAction(
            chat_id=..., action=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendChatAction, ok=True, result=None)

        response: bool = await bot.send_chat_action(
            chat_id=..., action=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendChatAction"
        # assert request.data == {}
        assert response == prepare_result.result
