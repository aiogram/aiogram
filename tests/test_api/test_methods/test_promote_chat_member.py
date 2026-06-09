from aiogram.methods import PromoteChatMember
from tests.mocked_bot import MockedBot


class TestPromoteChatMember:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(PromoteChatMember, ok=True, result=True)

        response: bool = await bot.promote_chat_member(
            chat_id=-42,
            user_id=42,
            can_manage_tags=True,
        )
        request = bot.get_request()
        assert request.can_manage_tags is True
        assert response == prepare_result.result
