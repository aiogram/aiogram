from typing import Union

from aiogram.methods import SetGameScore
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestSetGameScore:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetGameScore, ok=True, result=True)

        response: Union[Message, bool] = await bot.set_game_score(
            user_id=42, score=100500, inline_message_id="inline message"
        )
        request = bot.get_request()
        assert response == prepare_result.result
