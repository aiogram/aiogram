from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .chat import Chat
    from .chat_invite_link import ChatInviteLink
    from .chat_member_administrator import ChatMemberAdministrator
    from .chat_member_banned import ChatMemberBanned
    from .chat_member_left import ChatMemberLeft
    from .chat_member_member import ChatMemberMember
    from .chat_member_owner import ChatMemberOwner
    from .chat_member_restricted import ChatMemberRestricted
    from .user import User


class ChatMemberUpdated(TelegramObject):
    """
    This object represents changes in the status of a chat member.

    Source: https://core.telegram.org/bots/api#chatmemberupdated
    """

    chat: Chat
    """Chat the user belongs to"""
    from_user: User = Field(..., alias="from")
    """Performer of the action, which resulted in the change"""
    date: datetime.datetime
    """Date the change was done in Unix time"""
    old_chat_member: Union[
        ChatMemberOwner,
        ChatMemberAdministrator,
        ChatMemberMember,
        ChatMemberRestricted,
        ChatMemberLeft,
        ChatMemberBanned,
    ]
    """Previous information about the chat member"""
    new_chat_member: Union[
        ChatMemberOwner,
        ChatMemberAdministrator,
        ChatMemberMember,
        ChatMemberRestricted,
        ChatMemberLeft,
        ChatMemberBanned,
    ]
    """New information about the chat member"""
    invite_link: Optional[ChatInviteLink] = None
    """*Optional*. Chat invite link, which was used by the user to join the chat; for joining by invite link events only."""
