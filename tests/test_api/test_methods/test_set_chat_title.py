import pytest

from aiogram.api.methods import Request, SetChatTitle
from tests.mocked_bot import MockedBot


class TestSetChatTitle:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatTitle, ok=True, result=True)

        response: bool = await SetChatTitle(chat_id=-42, title="test chat")
        request: Request = bot.get_request()
        assert request.method == "setChatTitle"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatTitle, ok=True, result=True)

        response: bool = await bot.set_chat_title(chat_id=-42, title="test chat")
        request: Request = bot.get_request()
        assert request.method == "setChatTitle"
        assert response == prepare_result.result
