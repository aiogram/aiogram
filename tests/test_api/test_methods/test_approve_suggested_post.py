from aiogram.methods import ApproveSuggestedPost
from tests.mocked_bot import MockedBot


class TestApproveSuggestedPost:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(ApproveSuggestedPost, ok=True, result=True)

        response: bool = await bot.approve_suggested_post(
            chat_id=-42,
            message_id=42,
        )
        request = bot.get_request()
        assert response == prepare_result.result
