from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..enums import ChatMemberStatus
from .chat_member import ChatMember
from .user import User


class ChatMemberOwner(ChatMember, kw_only=True, tag=True):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that owns the chat and has all administrator privileges.

    Source: https://core.telegram.org/bots/api#chatmemberowner
    """

    status: str = ChatMemberStatus.CREATOR
    """The member's status in the chat, always 'creator'"""
    user: User
    """Information about the user"""
    is_anonymous: bool
    """:code:`True`, if the user's presence in the chat is hidden"""
    custom_title: Optional[str] = None
    """*Optional*. Custom title for this user"""
