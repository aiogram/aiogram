from __future__ import annotations

from typing import TYPE_CHECKING

from ..enums import ChatMemberStatus
from .chat_member import ChatMember
from .user import User


class ChatMemberMember(ChatMember, kw_only=True, tag=True):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that has no additional privileges or restrictions.

    Source: https://core.telegram.org/bots/api#chatmembermember
    """

    status: str = ChatMemberStatus.MEMBER
    """The member's status in the chat, always 'member'"""
    user: User
    """Information about the user"""
