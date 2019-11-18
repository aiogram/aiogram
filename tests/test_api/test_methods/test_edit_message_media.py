import pytest
from aiogram.api.methods import EditMessageMedia, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestEditMessageMedia:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageMedia, ok=True, result=None)

        response: Union[Message, bool] = await EditMessageMedia(media=...,)
        request: Request = bot.get_request()
        assert request.method == "editMessageMedia"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageMedia, ok=True, result=None)

        response: Union[Message, bool] = await bot.edit_message_media(media=...,)
        request: Request = bot.get_request()
        assert request.method == "editMessageMedia"
        # assert request.data == {}
        assert response == prepare_result.result
