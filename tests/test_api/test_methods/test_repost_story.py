from aiogram.methods import RepostStory
from aiogram.types import Chat, Story
from tests.mocked_bot import MockedBot


class TestRepostStory:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            RepostStory,
            ok=True,
            result=Story(
                id=42,
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Story = await bot.repost_story(
            business_connection_id="test_connection_id",
            from_chat_id=123,
            from_story_id=456,
            active_period=6 * 3600,
        )
        request = bot.get_request()
        assert response == prepare_result.result
