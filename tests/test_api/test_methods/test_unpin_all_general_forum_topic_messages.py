from aiogram.methods import (
    Request,
    UnpinAllForumTopicMessages,
    UnpinAllGeneralForumTopicMessages,
)
from tests.mocked_bot import MockedBot


class TestUnpinAllForumTopicMessages:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            UnpinAllGeneralForumTopicMessages, ok=True, result=True
        )

        response: bool = await bot.unpin_all_general_forum_topic_messages(
            chat_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
