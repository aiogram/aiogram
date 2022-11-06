from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class ChatMember(TelegramObject):
    """
    This object contains information about one member of a chat. Currently, the following 6 types of chat members are supported:

     - :class:`aiogram.types.chat_member_owner.ChatMemberOwner`
     - :class:`aiogram.types.chat_member_administrator.ChatMemberAdministrator`
     - :class:`aiogram.types.chat_member_member.ChatMemberMember`
     - :class:`aiogram.types.chat_member_restricted.ChatMemberRestricted`
     - :class:`aiogram.types.chat_member_left.ChatMemberLeft`
     - :class:`aiogram.types.chat_member_banned.ChatMemberBanned`

    Source: https://core.telegram.org/bots/api#chatmember
    """

    status: str
    """..."""
    user: Optional[User] = None
    """*Optional*. Information about the user"""
    is_anonymous: Optional[bool] = None
    """*Optional*. :code:`True`, if the user's presence in the chat is hidden"""
    custom_title: Optional[str] = None
    """*Optional*. Custom title for this user"""
    can_be_edited: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot is allowed to edit administrator privileges of that user"""
    can_manage_chat: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_delete_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can delete messages of other users"""
    can_manage_video_chats: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can manage video chats"""
    can_restrict_members: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can restrict, ban or unban chat members"""
    can_promote_members: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user)"""
    can_change_info: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to invite new users to the chat"""
    can_post_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can post in the channel; channels only"""
    can_edit_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can edit messages of other users and can pin messages; channels only"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to pin messages; groups and supergroups only"""
    can_manage_topics: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to create, rename, close, and reopen forum topics; supergroups only"""
    is_member: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is a member of the chat at the moment of the request"""
    can_send_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send text messages, contacts, locations and venues"""
    can_send_media_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes"""
    can_send_polls: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send polls"""
    can_send_other_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to send animations, games, stickers and use inline bots"""
    can_add_web_page_previews: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to add web page previews to their messages"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """*Optional*. Date when restrictions will be lifted for this user; unix time. If 0, then the user is restricted forever"""
