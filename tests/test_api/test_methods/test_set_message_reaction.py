from random import randint

from aiogram.methods import SetMessageReaction
from aiogram.types import ReactionTypeCustomEmoji
from tests.mocked_bot import MockedBot


class TestSetMessageReaction:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SetMessageReaction,
            ok=True,
            result=True,
        )

        response: bool = await bot.set_message_reaction(
            chat_id=randint(200, 300),
            message_id=randint(100, 200),
            reaction=[
                ReactionTypeCustomEmoji(custom_emoji_id="qwerty"),
            ],
        )
        request = bot.get_request()
        assert request
        assert response == prepare_result.result
