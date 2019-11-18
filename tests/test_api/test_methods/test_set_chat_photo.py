import pytest
from aiogram.api.methods import Request, SetChatPhoto
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSetChatPhoto:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPhoto, ok=True, result=None)

        response: bool = await SetChatPhoto(
            chat_id=..., photo=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPhoto"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPhoto, ok=True, result=None)

        response: bool = await bot.set_chat_photo(
            chat_id=..., photo=...,
        )
        request: Request = bot.get_request()
        assert request.method == "setChatPhoto"
        # assert request.data == {}
        assert response == prepare_result.result
