from typing import Union

import pytest

from aiogram.methods import Request, SetGameScore
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestSetGameScore:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetGameScore, ok=True, result=True)

        response: Union[Message, bool] = await SetGameScore(
            user_id=42, score=100500, inline_message_id="inline message"
        )
        request: Request = bot.get_request()
        assert request.method == "setGameScore"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetGameScore, ok=True, result=True)

        response: Union[Message, bool] = await bot.set_game_score(
            user_id=42, score=100500, inline_message_id="inline message"
        )
        request: Request = bot.get_request()
        assert request.method == "setGameScore"
        assert response == prepare_result.result
