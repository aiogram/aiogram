from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class ChatInviteLink(TelegramObject):
    """
    Represents an invite link for a chat.

    Source: https://core.telegram.org/bots/api#chatinvitelink
    """

    invite_link: str
    """The invite link. If the link was created by another chat administrator, then the second part of the link will be replaced with '…'."""
    creator: User
    """Creator of the link"""
    creates_join_request: bool
    """:code:`True`, if users joining the chat via the link need to be approved by chat administrators"""
    is_primary: bool
    """:code:`True`, if the link is primary"""
    is_revoked: bool
    """:code:`True`, if the link is revoked"""
    name: Optional[str] = None
    """*Optional*. Invite link name"""
    expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """*Optional*. Point in time (Unix timestamp) when the link will expire or has been expired"""
    member_limit: Optional[int] = None
    """*Optional*. Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999"""
    pending_join_request_count: Optional[int] = None
    """*Optional*. Number of pending join requests created using this link"""
