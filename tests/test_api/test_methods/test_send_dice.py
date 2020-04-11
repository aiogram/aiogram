import pytest

from aiogram.api.methods import Request, SendDice
from aiogram.api.types import Message
from tests.mocked_bot import MockedBot


class TestSendDice:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendDice, ok=True, result=None)

        response: Message = await SendDice(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "sendDice"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendDice, ok=True, result=None)

        response: Message = await bot.send_dice(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "sendDice"
        assert response == prepare_result.result
