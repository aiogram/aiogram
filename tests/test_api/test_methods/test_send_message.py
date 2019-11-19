import pytest

from aiogram.api.methods import Request, SendMessage
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendMessage, ok=True, result=None)

        response: Message = await SendMessage(chat_id=..., text=...)
        request: Request = bot.get_request()
        assert request.method == "sendMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendMessage, ok=True, result=None)

        response: Message = await bot.send_message(chat_id=..., text=...)
        request: Request = bot.get_request()
        assert request.method == "sendMessage"
        # assert request.data == {}
        assert response == prepare_result.result
