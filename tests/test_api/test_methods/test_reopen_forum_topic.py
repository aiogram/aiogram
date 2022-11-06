import pytest

from aiogram.methods import ReopenForumTopic, Request
from tests.mocked_bot import MockedBot


class TestReopenForumTopic:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReopenForumTopic, ok=True, result=None)

        response: bool = await ReopenForumTopic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "reopenForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ReopenForumTopic, ok=True, result=None)

        response: bool = await bot.reopen_forum_topic(
            chat_id=42,
            message_thread_id=42,
        )
        request: Request = bot.get_request()
        assert request.method == "reopenForumTopic"
        # assert request.data == {}
        assert response == prepare_result.result
