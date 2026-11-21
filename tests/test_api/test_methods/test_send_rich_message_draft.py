from aiogram.methods import SendRichMessageDraft
from aiogram.types import InputRichMessage
from tests.mocked_bot import MockedBot


class TestSendRichMessageDraft:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SendRichMessageDraft, ok=True, result=True)

        response: bool = await bot.send_rich_message_draft(
            chat_id=42,
            draft_id=1,
            rich_message=InputRichMessage(html="<p>Draft</p>"),
        )
        bot.get_request()
        assert response == prepare_result.result
