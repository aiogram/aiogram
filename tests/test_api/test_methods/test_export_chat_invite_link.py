import pytest
from aiogram.api.methods import ExportChatInviteLink, Request
from tests.mocked_bot import MockedBot


@pytest.mark.skip
class TestExportChatInviteLink:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ExportChatInviteLink, ok=True, result=None)

        response: str = await ExportChatInviteLink(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "exportChatInviteLink"
        # assert request.data == {}
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ExportChatInviteLink, ok=True, result=None)

        response: str = await bot.export_chat_invite_link(chat_id=...,)
        request: Request = bot.get_request()
        assert request.method == "exportChatInviteLink"
        # assert request.data == {}
        assert response == prepare_result.result
