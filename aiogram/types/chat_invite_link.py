from datetime import datetime

from . import base
from . import fields
from .user import User


class ChatInviteLink(base.TelegramObject):
    """
    Represents an invite link for a chat.

    https://core.telegram.org/bots/api#chatinvitelink
    """

    invite_link: base.String = fields.Field()
    creator: User = fields.Field(base=User)
    is_primary: base.Boolean = fields.Field()
    is_revoked: base.Boolean = fields.Field()
    name: base.String = fields.Field()
    expire_date: datetime = fields.DateTimeField()
    member_limit: base.Integer = fields.Field()
    creates_join_request: datetime = fields.DateTimeField()
    pending_join_request_count: base.Integer = fields.Field()
