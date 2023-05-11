from __future__ import annotations

from typing import TYPE_CHECKING

from ..enums import ChatMemberStatus
from .chat_member import ChatMember
from .user import User


class ChatMemberLeft(ChatMember, kw_only=True, tag=True):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that isn't currently a member of the chat, but may join it themselves.

    Source: https://core.telegram.org/bots/api#chatmemberleft
    """

    status: str = ChatMemberStatus.LEFT
    """The member's status in the chat, always 'left'"""
    user: User
    """Information about the user"""
