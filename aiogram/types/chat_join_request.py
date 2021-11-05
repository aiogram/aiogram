from datetime import datetime

from . import base
from . import fields
from .user import User
from .chat import Chat
from .chat_invite_link import ChatInviteLink


class ChatJoinRequest(base.TelegramObject):
    """
    Represents a join request sent to a chat.

    https://core.telegram.org/bots/api#chatinvitelink
    """

    chat: Chat = fields.Field(base=Chat)
    from_user: User = fields.Field(alias="from", base=User)
    date: datetime = fields.DateTimeField()
    bio: base.String = fields.Field()
    invite_link: ChatInviteLink = fields.Field(base=ChatInviteLink)
