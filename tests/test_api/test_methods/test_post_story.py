import datetime

from aiogram.methods import PostStory
from aiogram.types import Chat, InputStoryContentPhoto, Story
from tests.mocked_bot import MockedBot


class TestPostStory:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            PostStory,
            ok=True,
            result=Story(
                id=42,
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Story = await bot.post_story(
            business_connection_id="test_connection_id",
            content=InputStoryContentPhoto(type="photo", photo="test_photo"),
            active_period=6 * 3600,  # 6 hours
            caption="Test story caption",
        )
        request = bot.get_request()
        assert response == prepare_result.result
