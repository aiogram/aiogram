import datetime

from aiogram.utils import helper
from . import base
from . import fields
from .user import User


class ChatMember(base.TelegramObject):
    """
    This object contains information about one member of a chat.

    https://core.telegram.org/bots/api#chatmember
    """
    user: User = fields.Field(base=User)
    status: base.String = fields.Field()
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
    can_send_messages: base.Boolean = fields.Field()
    can_send_media_messages: base.Boolean = fields.Field()
    can_send_other_messages: base.Boolean = fields.Field()
    can_add_web_page_previews: base.Boolean = fields.Field()

    def __hash__(self):
        return self.user.id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.user.id == self.user.id
        return self.user.id == other

    def __int__(self):
        return self.user.id


class ChatMemberStatus(helper.Helper):
    """
    Chat member status
    """

    mode = helper.HelperMode.lowercase

    CREATOR = helper.Item()  # creator
    ADMINISTRATOR = helper.Item()  # administrator
    MEMBER = helper.Item()  # member
    LEFT = helper.Item()  # left
    KICKED = helper.Item()  # kicked

    @classmethod
    def is_admin(cls, role):
        return role in [cls.ADMINISTRATOR, cls.CREATOR]

    @classmethod
    def is_member(cls, role):
        return role in [cls.MEMBER, cls.ADMINISTRATOR, cls.CREATOR]
