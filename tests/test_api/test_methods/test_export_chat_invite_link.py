from aiogram.methods import ExportChatInviteLink
from tests.mocked_bot import MockedBot


class TestExportChatInviteLink:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            ExportChatInviteLink, ok=True, result="http://example.com"
        )

        response: str = await bot.export_chat_invite_link(chat_id=42)
        bot.get_request()
        assert response == prepare_result.result
