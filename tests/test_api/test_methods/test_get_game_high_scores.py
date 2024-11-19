from typing import List

from aiogram.methods import GetGameHighScores
from aiogram.types import GameHighScore, User
from tests.mocked_bot import MockedBot


class TestGetGameHighScores:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetGameHighScores,
            ok=True,
            result=[
                GameHighScore(
                    position=1, user=User(id=42, is_bot=False, first_name="User"), score=42
                )
            ],
        )

        response: List[GameHighScore] = await bot.get_game_high_scores(user_id=42)
        request = bot.get_request()
        assert response == prepare_result.result
