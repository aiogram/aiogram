from datetime import datetime

from . import base
from . import fields
from .chat import Chat
from .chat_invite_link import ChatInviteLink
from .user import User


class ChatJoinRequest(base.TelegramObject):
    """
    Represents a join request sent to a chat.

    https://core.telegram.org/bots/api#chatjoinrequest
    """

    chat: Chat = fields.Field(base=Chat)
    from_user: User = fields.Field(alias="from", base=User)
    date: datetime = fields.DateTimeField()
    bio: base.String = fields.Field()
    invite_link: ChatInviteLink = fields.Field(base=ChatInviteLink)

    async def approve(self) -> base.Boolean:
        return await self.bot.approve_chat_join_request(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
        )

    async def decline(self) -> base.Boolean:
        return await self.bot.decline_chat_join_request(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
        )
