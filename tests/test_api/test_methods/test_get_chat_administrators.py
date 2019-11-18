import pytest
from aiogram.api.methods import GetChatAdministrators, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestGetChatAdministrators:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatAdministrators, ok=True, result=None)

        response: List[ChatMember] = await GetChatAdministrators(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChatAdministrators"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetChatAdministrators, ok=True, result=None)

        response: List[ChatMember] = await bot.get_chat_administrators(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "getChatAdministrators"
        # assert request.data == {}
        assert response == prepare_result.result
