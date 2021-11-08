from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import ApproveChatJoinRequest, DeclineChatJoinRequest

if TYPE_CHECKING:
    from .chat import Chat
    from .chat_invite_link import ChatInviteLink
    from .user import User


class ChatJoinRequest(TelegramObject):
    """
    Represents a join request sent to a chat.

    Source: https://core.telegram.org/bots/api#chatjoinrequest
    """

    chat: Chat
    """Chat to which the request was sent"""
    from_user: User = Field(..., alias="from")
    """User that sent the join request"""
    date: datetime.datetime
    """Date the request was sent in Unix time"""
    bio: Optional[str] = None
    """*Optional*. Bio of the user."""
    invite_link: Optional[ChatInviteLink] = None
    """*Optional*. Chat invite link that was used by the user to send the join request"""

    def approve(self) -> ApproveChatJoinRequest:
        """
        Use this method to approve a chat join request.
        """
        from ..methods import ApproveChatJoinRequest

        return ApproveChatJoinRequest(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
        )

    def decline(self) -> DeclineChatJoinRequest:
        """
        Use this method to decline a chat join request.
        """
        from ..methods import DeclineChatJoinRequest

        return DeclineChatJoinRequest(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
        )
