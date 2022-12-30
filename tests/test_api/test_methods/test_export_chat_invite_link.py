from aiogram.methods import ExportChatInviteLink, Request
from tests.mocked_bot import MockedBot


class TestExportChatInviteLink:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ExportChatInviteLink, ok=True, result="http://example.com"
        )

        response: str = await ExportChatInviteLink(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "exportChatInviteLink"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ExportChatInviteLink, ok=True, result="http://example.com"
        )

        response: str = await bot.export_chat_invite_link(chat_id=42)
        request: Request = bot.get_request()
        assert request.method == "exportChatInviteLink"
        assert response == prepare_result.result
