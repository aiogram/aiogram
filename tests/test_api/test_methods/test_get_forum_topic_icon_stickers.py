from typing import List

from aiogram.methods import GetForumTopicIconStickers, Request
from aiogram.types import Sticker
from tests.mocked_bot import MockedBot


class TestGetForumTopicIconStickers:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetForumTopicIconStickers, ok=True, result=[])

        response: List[Sticker] = await GetForumTopicIconStickers()
        request: Request = bot.get_request()
        assert request.method == "getForumTopicIconStickers"
        # assert request.data == {}
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(GetForumTopicIconStickers, ok=True, result=[])

        response: List[Sticker] = await bot.get_forum_topic_icon_stickers()
        request: Request = bot.get_request()
        assert request.method == "getForumTopicIconStickers"
        # assert request.data == {}
        assert response == prepare_result.result
