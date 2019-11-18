import pytest

from aiogram.api.methods import Request, SetChatDescription
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetChatDescription:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatDescription, ok=True, result=None)

        response: bool = await SetChatDescription(chat_id=...)
        request: Request = bot.get_request()
        assert request.method == "setChatDescription"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatDescription, ok=True, result=None)

        response: bool = await bot.set_chat_description(chat_id=...)
        request: Request = bot.get_request()
        assert request.method == "setChatDescription"
        # assert request.data == {}
        assert response == prepare_result.result
