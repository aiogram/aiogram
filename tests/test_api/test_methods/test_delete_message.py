import pytest
from aiogram.api.methods import DeleteMessage, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestDeleteMessage:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMessage, ok=True, result=None)

        response: bool = await DeleteMessage(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "deleteMessage"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(DeleteMessage, ok=True, result=None)

        response: bool = await bot.delete_message(
            chat_id=..., message_id=...,
        )
        request: Request = bot.get_request()
        assert request.method == "deleteMessage"
        # assert request.data == {}
        assert response == prepare_result.result
