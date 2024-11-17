from typing import List

from aiogram.methods import GetForumTopicIconStickers
from aiogram.types import Sticker
from tests.mocked_bot import MockedBot


class TestGetForumTopicIconStickers:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetForumTopicIconStickers, ok=True, result=[])

        response: List[Sticker] = await bot.get_forum_topic_icon_stickers()
        request = bot.get_request()
        assert response == prepare_result.result
