from aiogram.methods import SetChatPermissions
from aiogram.types import ChatPermissions
from tests.mocked_bot import MockedBot


class TestSetChatPermissions:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(SetChatPermissions, ok=True, result=True)

        response: bool = await bot.set_chat_permissions(
            chat_id=-42, permissions=ChatPermissions(can_send_messages=False)
        )
        bot.get_request()
        assert response == prepare_result.result
