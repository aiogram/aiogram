from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ..enums import ChatMemberStatus
from .chat_member import ChatMember

if TYPE_CHECKING:
    from .user import User


class ChatMemberMember(ChatMember):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that has no additional privileges or restrictions.

    Source: https://core.telegram.org/bots/api#chatmembermember
    """

    status: str = Field(ChatMemberStatus.MEMBER, const=True)
    """The member's status in the chat, always 'member'"""
    user: User
    """Information about the user"""
