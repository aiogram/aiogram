import datetime

from aiogram.methods import EditStory
from aiogram.types import Chat, InputStoryContentPhoto, Story
from tests.mocked_bot import MockedBot


class TestEditStory:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            EditStory,
            ok=True,
            result=Story(
                id=42,
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Story = await bot.edit_story(
            business_connection_id="test_connection_id",
            story_id=42,
            content=InputStoryContentPhoto(type="photo", photo="test_photo"),
            caption="Test caption",
        )
        request = bot.get_request()
        assert response == prepare_result.result
