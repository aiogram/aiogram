import datetime
from typing import Optional

from . import base, fields
from .user import User
from ..utils import helper


class ChatMemberStatus(helper.Helper):
    """
    Chat member status
    """
    mode = helper.HelperMode.lowercase

    CREATOR = helper.Item()  # creator
    OWNER = CREATOR  # creator
    ADMINISTRATOR = helper.Item()  # administrator
    MEMBER = helper.Item()  # member
    RESTRICTED = helper.Item()  # restricted
    LEFT = helper.Item()  # left
    KICKED = helper.Item()  # kicked
    BANNED = KICKED  # kicked

    @classmethod
    def is_chat_creator(cls, role: str) -> bool:
        return role == cls.CREATOR

    @classmethod
    def is_chat_admin(cls, role: str) -> bool:
        return role in (cls.ADMINISTRATOR, cls.CREATOR)

    @classmethod
    def is_chat_member(cls, role: str) -> bool:
        return role in (cls.MEMBER, cls.ADMINISTRATOR, cls.CREATOR, cls.RESTRICTED)

    @classmethod
    def get_class_by_status(cls, status: str) -> Optional["ChatMember"]:
        return {
            cls.OWNER: ChatMemberOwner,
            cls.ADMINISTRATOR: ChatMemberAdministrator,
            cls.MEMBER: ChatMemberMember,
            cls.RESTRICTED: ChatMemberRestricted,
            cls.LEFT: ChatMemberLeft,
            cls.BANNED: ChatMemberBanned,
        }.get(status)


class ChatMember(base.TelegramObject):
    """
    This object contains information about one member of a chat.
    Currently, the following 6 types of chat members are supported:
        ChatMemberOwner
        ChatMemberAdministrator
        ChatMemberMember
        ChatMemberRestricted
        ChatMemberLeft
        ChatMemberBanned

    https://core.telegram.org/bots/api#chatmember
    """
    status: base.String = fields.Field()
    user: User = fields.Field(base=User)

    def __int__(self) -> int:
        return self.user.id

    @classmethod
    def resolve(cls, **kwargs) -> "ChatMember":
        status = kwargs.get("status")
        mapping = {
            ChatMemberStatus.OWNER: ChatMemberOwner,
            ChatMemberStatus.ADMINISTRATOR: ChatMemberAdministrator,
            ChatMemberStatus.MEMBER: ChatMemberMember,
            ChatMemberStatus.RESTRICTED: ChatMemberRestricted,
            ChatMemberStatus.LEFT: ChatMemberLeft,
            ChatMemberStatus.BANNED: ChatMemberBanned,
        }
        class_ = mapping.get(status)
        if class_ is None:
            raise ValueError(f"Can't find `ChatMember` class for status `{status}`")

        return class_(**kwargs)


class ChatMemberOwner(ChatMember):
    """
    Represents a chat member that owns the chat and has all
    administrator privileges.
    https://core.telegram.org/bots/api#chatmemberowner
    """
    status: base.String = fields.Field(default=ChatMemberStatus.OWNER)
    user: User = fields.Field(base=User)
    custom_title: base.String = fields.Field()
    is_anonymous: base.Boolean = fields.Field()


class ChatMemberAdministrator(ChatMember):
    """
    Represents a chat member that has some additional privileges.

    https://core.telegram.org/bots/api#chatmemberadministrator
    """
    status: base.String = fields.Field(default=ChatMemberStatus.ADMINISTRATOR)
    user: User = fields.Field(base=User)
    can_be_edited: base.Boolean = fields.Field()
    custom_title: base.String = fields.Field()
    is_anonymous: base.Boolean = fields.Field()
    can_manage_chat: base.Boolean = fields.Field()
    can_post_messages: base.Boolean = fields.Field()
    can_edit_messages: base.Boolean = fields.Field()
    can_delete_messages: base.Boolean = fields.Field()
    can_manage_voice_chats: base.Boolean = fields.Field()
    can_restrict_members: base.Boolean = fields.Field()
    can_promote_members: base.Boolean = fields.Field()
    can_change_info: base.Boolean = fields.Field()
    can_invite_users: base.Boolean = fields.Field()
    can_pin_messages: base.Boolean = fields.Field()


class ChatMemberMember(ChatMember):
    """
    Represents a chat member that has no additional privileges or
    restrictions.

    https://core.telegram.org/bots/api#chatmembermember
    """
    status: base.String = fields.Field(default=ChatMemberStatus.MEMBER)
    user: User = fields.Field(base=User)


class ChatMemberRestricted(ChatMember):
    """
    Represents a chat member that is under certain restrictions in the
    chat. Supergroups only.

    https://core.telegram.org/bots/api#chatmemberrestricted
    """
    status: base.String = fields.Field(default=ChatMemberStatus.RESTRICTED)
    user: User = fields.Field(base=User)
    is_member: base.Boolean = fields.Field()
    can_change_info: base.Boolean = fields.Field()
    can_invite_users: base.Boolean = fields.Field()
    can_pin_messages: base.Boolean = fields.Field()
    can_send_messages: base.Boolean = fields.Field()
    can_send_media_messages: base.Boolean = fields.Field()
    can_send_polls: base.Boolean = fields.Field()
    can_send_other_messages: base.Boolean = fields.Field()
    can_add_web_page_previews: base.Boolean = fields.Field()
    until_date: datetime.datetime = fields.DateTimeField()


class ChatMemberLeft(ChatMember):
    """
    Represents a chat member that isn't currently a member of the chat,
    but may join it themselves.

    https://core.telegram.org/bots/api#chatmemberleft
    """
    status: base.String = fields.Field(default=ChatMemberStatus.LEFT)
    user: User = fields.Field(base=User)


class ChatMemberBanned(ChatMember):
    """
    Represents a chat member that was banned in the chat and can't
    return to the chat or view chat messages.

    https://core.telegram.org/bots/api#chatmemberbanned
    """
    status: base.String = fields.Field(default=ChatMemberStatus.BANNED)
    user: User = fields.Field(base=User)
    until_date: datetime.datetime = fields.DateTimeField()
