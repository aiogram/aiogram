import datetime

from . import base
from . import fields
from .user import User
from ..utils import helper


class ChatMember(base.TelegramObject):
    """
    This object contains information about one member of a chat.

    https://core.telegram.org/bots/api#chatmember
    """
    user: User = fields.Field(base=User)
    status: base.String = fields.Field()
    custom_title: base.String = fields.Field()
    is_anonymous: base.Boolean = fields.Field()
    until_date: datetime.datetime = fields.DateTimeField()
    can_be_edited: base.Boolean = fields.Field()
    can_change_info: base.Boolean = fields.Field()
    can_post_messages: base.Boolean = fields.Field()
    can_edit_messages: base.Boolean = fields.Field()
    can_delete_messages: base.Boolean = fields.Field()
    can_invite_users: base.Boolean = fields.Field()
    can_restrict_members: base.Boolean = fields.Field()
    can_pin_messages: base.Boolean = fields.Field()
    can_promote_members: base.Boolean = fields.Field()
    is_member: base.Boolean = fields.Field()
    can_send_messages: base.Boolean = fields.Field()
    can_send_media_messages: base.Boolean = fields.Field()
    can_send_polls: base.Boolean = fields.Field()
    can_send_other_messages: base.Boolean = fields.Field()
    can_add_web_page_previews: base.Boolean = fields.Field()

    def is_chat_creator(self) -> bool:
        return ChatMemberStatus.is_chat_creator(self.status)

    def is_chat_admin(self) -> bool:
        return ChatMemberStatus.is_chat_admin(self.status)

    def is_chat_member(self) -> bool:
        return ChatMemberStatus.is_chat_member(self.status)

    def __int__(self) -> int:
        return self.user.id


class ChatMemberStatus(helper.Helper):
    """
    Chat member status
    """
    mode = helper.HelperMode.lowercase

    CREATOR = helper.Item()  # creator
    ADMINISTRATOR = helper.Item()  # administrator
    MEMBER = helper.Item()  # member
    RESTRICTED = helper.Item()  # restricted
    LEFT = helper.Item()  # left
    KICKED = helper.Item()  # kicked

    @classmethod
    def is_chat_creator(cls, role: str) -> bool:
        return role == cls.CREATOR

    @classmethod
    def is_chat_admin(cls, role: str) -> bool:
        return role in (cls.ADMINISTRATOR, cls.CREATOR)

    @classmethod
    def is_chat_member(cls, role: str) -> bool:
        return role in (cls.MEMBER, cls.ADMINISTRATOR, cls.CREATOR, cls.RESTRICTED)
