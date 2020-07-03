import pytest

from aiogram.api.methods import GetChat, Request
from aiogram.api.types import Chat
from aiogram.api.types.chat import ChatType
from tests.factories.chat import ChatFactory
from tests.mocked_bot import MockedBot


class TestGetChat:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        channel = ChatFactory(type=ChatType.CHANNEL)
        prepare_result = bot.add_result_for(
            GetChat, ok=True, result=channel
        )

        response: Chat = await GetChat(chat_id=channel.id)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        channel = ChatFactory(type=ChatType.CHANNEL)
        prepare_result = bot.add_result_for(
            GetChat, ok=True, result=channel
        )

        response: Chat = await bot.get_chat(chat_id=channel.id)
        request: Request = bot.get_request()
        assert request.method == "getChat"
        assert response == prepare_result.result
