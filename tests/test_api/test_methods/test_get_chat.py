import pytest
from aiogram.api.methods import GetChat, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetChat:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChat, ok=True, result=None)

        response: Chat = await GetChat(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChat, ok=True, result=None)

        response: Chat = await bot.get_chat(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        # assert request.data == {}
        assert response == prepare_result.result
