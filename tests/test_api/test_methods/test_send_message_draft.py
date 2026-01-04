from aiogram.methods import SendMessageDraft
from tests.mocked_bot import MockedBot


class TestSendMessageDraft:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendMessageDraft,
            ok=True,
            result=True,
        )

        response: bool = await bot.send_message_draft(
            chat_id=42,
            draft_id=1,
            text="test draft",
        )
        bot.get_request()
        assert response == prepare_result.result
