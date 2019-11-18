import pytest
from aiogram.api.methods import Request, SendPhoto
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendPhoto:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendPhoto, ok=True, result=None)

        response: Message = await SendPhoto(
            chat_id=..., photo=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendPhoto"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendPhoto, ok=True, result=None)

        response: Message = await bot.send_photo(
            chat_id=..., photo=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendPhoto"
        # assert request.data == {}
        assert response == prepare_result.result
