import pytest
from aiogram.api.methods import EditMessageText, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestEditMessageText:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageText, ok=True, result=None)

        response: Union[Message, bool] = await EditMessageText(text=...,)
        request: Request = bot.get_request()
        assert request.method == "editMessageText"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageText, ok=True, result=None)

        response: Union[Message, bool] = await bot.edit_message_text(text=...,)
        request: Request = bot.get_request()
        assert request.method == "editMessageText"
        # assert request.data == {}
        assert response == prepare_result.result
