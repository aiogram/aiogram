import pytest
from aiogram.api.methods import EditMessageReplyMarkup, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestEditMessageReplyMarkup:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageReplyMarkup, ok=True, result=None)

        response: Union[Message, bool] = await EditMessageReplyMarkup()
        request: Request = bot.get_request()
        assert request.method == "editMessageReplyMarkup"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageReplyMarkup, ok=True, result=None)

        response: Union[Message, bool] = await bot.edit_message_reply_markup()
        request: Request = bot.get_request()
        assert request.method == "editMessageReplyMarkup"
        # assert request.data == {}
        assert response == prepare_result.result
