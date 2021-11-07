from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Union

from pydantic import Field

from .chat_member import ChatMember

if TYPE_CHECKING:
    from .user import User


class ChatMemberBanned(ChatMember):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that was banned in the chat and can't return to the chat or view chat messages.

    Source: https://core.telegram.org/bots/api#chatmemberbanned
    """

    status: str = Field("kicked", const=True)
    """The member's status in the chat, always 'kicked'"""
    user: User
    """Information about the user"""
    until_date: Union[datetime.datetime, datetime.timedelta, int]
    """Date when restrictions will be lifted for this user; unix time. If 0, then the user is banned forever"""
