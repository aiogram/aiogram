from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Union

from pydantic import Field

from .chat_member import ChatMember

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class ChatMemberRestricted(ChatMember):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that is under certain restrictions in the chat. Supergroups only.

    Source: https://core.telegram.org/bots/api#chatmemberrestricted
    """

    status: str = Field("restricted", const=True)
    """The member's status in the chat, always 'restricted'"""
    user: User
    """Information about the user"""
    is_member: bool
    """True, if the user is a member of the chat at the moment of the request"""
    can_change_info: bool
    """True, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: bool
    """True, if the user is allowed to invite new users to the chat"""
    can_pin_messages: bool
    """True, if the user is allowed to pin messages; groups and supergroups only"""
    can_send_messages: bool
    """True, if the user is allowed to send text messages, contacts, locations and venues"""
    can_send_media_messages: bool
    """True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes"""
    can_send_polls: bool
    """True, if the user is allowed to send polls"""
    can_send_other_messages: bool
    """True, if the user is allowed to send animations, games, stickers and use inline bots"""
    can_add_web_page_previews: bool
    """True, if the user is allowed to add web page previews to their messages"""
    until_date: Union[datetime.datetime, datetime.timedelta, int]
    """Date when restrictions will be lifted for this user; unix time"""
