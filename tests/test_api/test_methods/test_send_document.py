import pytest
from aiogram.api.methods import Request, SendDocument
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendDocument:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendDocument, ok=True, result=None)

        response: Message = await SendDocument(
            chat_id=..., document=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendDocument"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendDocument, ok=True, result=None)

        response: Message = await bot.send_document(
            chat_id=..., document=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendDocument"
        # assert request.data == {}
        assert response == prepare_result.result
