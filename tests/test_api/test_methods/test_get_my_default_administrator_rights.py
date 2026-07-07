from aiogram.methods import GetMyDefaultAdministratorRights
from aiogram.types import ChatAdministratorRights
from tests.mocked_bot import MockedBot


class TestGetMyDefaultAdministratorRights:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetMyDefaultAdministratorRights,
            ok=True,
            result=ChatAdministratorRights(
                is_anonymous=False,
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_post_stories=False,
                can_edit_stories=False,
                can_delete_stories=False,
            ),
        )

        response: ChatAdministratorRights = await bot.get_my_default_administrator_rights()
        bot.get_request()
        assert response == prepare_result.result
