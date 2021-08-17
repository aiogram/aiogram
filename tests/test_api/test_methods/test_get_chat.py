import pytest

from aiogram.methods import GetChat, Request
from aiogram.types import Chat
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class TestGetChat:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChat, ok=True, result=Chat(id=-42, type="channel", title="chat")
        )

        response: Chat = await GetChat(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChat, ok=True, result=Chat(id=-42, type="channel", title="chat")
        )

        response: Chat = await bot.get_chat(chat_id=-42)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        assert response == prepare_result.result
