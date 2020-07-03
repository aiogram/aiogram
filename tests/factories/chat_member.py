import factory

from aiogram.api.types.chat_member import ChatMemberStatus
from tests.factories.user import UserFactory


class ChatMemberFactory(factory.Factory):
    user = factory.SubFactory(UserFactory)

    status = ChatMemberStatus.ADMINISTRATOR
    can_be_edited = False
    can_change_info = True
    can_delete_messages = True
    can_invite_users = True
    can_restrict_members = True
    can_pin_messages = True
    can_promote_members = False
