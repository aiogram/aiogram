import pytest
from aiogram.api.methods import Request, SendVideoNote
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestSendVideoNote:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVideoNote, ok=True, result=None)

        response: Message = await SendVideoNote(
            chat_id=..., video_note=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendVideoNote, ok=True, result=None)

        response: Message = await bot.send_video_note(
            chat_id=..., video_note=...,
        )
        request: Request = bot.get_request()
        assert request.method == "sendVideoNote"
        # assert request.data == {}
        assert response == prepare_result.result
