from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

from aiogram.utils import helper

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class ChatMember(TelegramObject):
    """
    This object contains information about one member of a chat.

    Source: https://core.telegram.org/bots/api#chatmember
    """

    user: User
    """Information about the user"""
    status: str
    """The member's status in the chat. Can be 'creator', 'administrator', 'member', 'restricted', 'left' or 'kicked'"""
    custom_title: Optional[str] = None
    """*Optional*. Owner and administrators only. Custom title for this user"""
    is_anonymous: Optional[bool] = None
    """*Optional*. Owner and administrators only. True, if the user's presence in the chat is hidden"""
    can_be_edited: Optional[bool] = None
    """*Optional*. Administrators only. True, if the bot is allowed to edit administrator privileges of that user"""
    can_manage_chat: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_post_messages: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can post in the channel; channels only"""
    can_edit_messages: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can edit messages of other users and can pin messages; channels only"""
    can_delete_messages: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can delete messages of other users"""
    can_manage_voice_chats: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can manage voice chats"""
    can_restrict_members: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can restrict, ban or unban chat members"""
    can_promote_members: Optional[bool] = None
    """*Optional*. Administrators only. True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user)"""
    can_change_info: Optional[bool] = None
    """*Optional*. Administrators and restricted only. True, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: Optional[bool] = None
    """*Optional*. Administrators and restricted only. True, if the user is allowed to invite new users to the chat"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. Administrators and restricted only. True, if the user is allowed to pin messages; groups and supergroups only"""
    is_member: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is a member of the chat at the moment of the request"""
    can_send_messages: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is allowed to send text messages, contacts, locations and venues"""
    can_send_media_messages: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes"""
    can_send_polls: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is allowed to send polls"""
    can_send_other_messages: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is allowed to send animations, games, stickers and use inline bots"""
    can_add_web_page_previews: Optional[bool] = None
    """*Optional*. Restricted only. True, if the user is allowed to add web page previews to their messages"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """*Optional*. Restricted and kicked only. Date when restrictions will be lifted for this user; unix time"""

    @property
    def is_chat_admin(self) -> bool:
        return self.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}

    @property
    def is_chat_member(self) -> bool:
        return self.status not in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}


class ChatMemberStatus(helper.Helper):
    """
    Chat member status
    """

    mode = helper.HelperMode.lowercase

    CREATOR = helper.Item()  # creator
    ADMINISTRATOR = helper.Item()  # administrator
    MEMBER = helper.Item()  # member
    RESTRICTED = helper.Item()  # restricted
    LEFT = helper.Item()  # left
    KICKED = helper.Item()  # kicked
