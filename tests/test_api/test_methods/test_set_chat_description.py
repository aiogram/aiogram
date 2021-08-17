import pytest

from aiogram.methods import Request, SetChatDescription
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestSetChatDescription:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatDescription, ok=True, result=True)

        response: bool = await SetChatDescription(chat_id=-42, description="awesome chat")
        request: Request = bot.get_request()
        assert request.method == "setChatDescription"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatDescription, ok=True, result=True)

        response: bool = await bot.set_chat_description(chat_id=-42, description="awesome chat")
        request: Request = bot.get_request()
        assert request.method == "setChatDescription"
        assert response == prepare_result.result
