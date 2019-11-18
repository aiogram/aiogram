import pytest
from aiogram.api.methods import EditMessageCaption, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestEditMessageCaption:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageCaption, ok=True, result=None)

        response: Union[Message, bool] = await EditMessageCaption()
        request: Request = bot.get_request()
        assert request.method == "editMessageCaption"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageCaption, ok=True, result=None)

        response: Union[Message, bool] = await bot.edit_message_caption()
        request: Request = bot.get_request()
        assert request.method == "editMessageCaption"
        # assert request.data == {}
        assert response == prepare_result.result
