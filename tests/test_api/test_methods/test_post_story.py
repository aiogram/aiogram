import json
from collections.abc import AsyncIterable

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import PostStory
from aiogram.types import BufferedInputFile, Chat, InputStoryContentPhoto, Story
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
        bot.get_request()
        assert response == prepare_result.result

    def test_upload_photo_form_data(self, bot: MockedBot):
        # The story photo can only be uploaded, so it must be sent as an attached file.
        method = PostStory(
            business_connection_id="test_connection_id",
            content=InputStoryContentPhoto(photo=BufferedInputFile(b"data", filename="a.jpg")),
            active_period=6 * 3600,
        )
        fields = AiohttpSession().build_form_data(bot, method)._fields

        content = next(value for info, _, value in fields if info["name"] == "content")
        attach = json.loads(content)["photo"]
        assert attach.startswith("attach://")
        file_info, _, file_value = fields[-1]
        assert file_info["name"] == attach.removeprefix("attach://")
        assert file_info["filename"] == "a.jpg"
        assert isinstance(file_value, AsyncIterable)
