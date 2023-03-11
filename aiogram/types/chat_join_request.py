from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional

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
    user_chat_id: int
    """Identifier of a private chat with the user who sent the join request. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier. The bot can use this identifier for 24 hours to send messages until the join request is processed, assuming no other administrator contacted the user."""
    date: datetime.datetime
    """Date the request was sent in Unix time"""
    bio: Optional[str] = None
    """*Optional*. Bio of the user."""
    invite_link: Optional[ChatInviteLink] = None
    """*Optional*. Chat invite link that was used by the user to send the join request"""

    def approve(
        self,
        **kwargs: Any,
    ) -> ApproveChatJoinRequest:
        """
        Shortcut for method :class:`aiogram.methods.approve_chat_join_request.ApproveChatJoinRequest`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`user_id`

        Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#approvechatjoinrequest

        :return: instance of method :class:`aiogram.methods.approve_chat_join_request.ApproveChatJoinRequest`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import ApproveChatJoinRequest

        return ApproveChatJoinRequest(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
            **kwargs,
        )

    def decline(
        self,
        **kwargs: Any,
    ) -> DeclineChatJoinRequest:
        """
        Shortcut for method :class:`aiogram.methods.decline_chat_join_request.DeclineChatJoinRequest`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`user_id`

        Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#declinechatjoinrequest

        :return: instance of method :class:`aiogram.methods.decline_chat_join_request.DeclineChatJoinRequest`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeclineChatJoinRequest

        return DeclineChatJoinRequest(
            chat_id=self.chat.id,
            user_id=self.from_user.id,
            **kwargs,
        )
