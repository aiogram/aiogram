import pytest

from aiogram.api.methods import Request, SendSticker
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendSticker:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendSticker, ok=True, result=None)

        response: Message = await SendSticker(chat_id=..., sticker=...)
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendSticker, ok=True, result=None)

        response: Message = await bot.send_sticker(chat_id=..., sticker=...)
        request: Request = bot.get_request()
        assert request.method == "sendSticker"
        # assert request.data == {}
        assert response == prepare_result.result
