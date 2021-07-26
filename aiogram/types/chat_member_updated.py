import datetime

from . import base
from . import fields
from .chat import Chat
from .chat_invite_link import ChatInviteLink
from .chat_member import ChatMember
from .user import User


class ChatMemberUpdated(base.TelegramObject):
    """
    This object represents changes in the status of a chat member.

    https://core.telegram.org/bots/api#chatmemberupdated
    """
    chat: Chat = fields.Field(base=Chat)
    from_user: User = fields.Field(alias="from", base=User)
    date: datetime.datetime = fields.DateTimeField()
    old_chat_member: ChatMember = fields.Field(base=ChatMember)
    new_chat_member: ChatMember = fields.Field(base=ChatMember)
    invite_link: ChatInviteLink = fields.Field(base=ChatInviteLink)
