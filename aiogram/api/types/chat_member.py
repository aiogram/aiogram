from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramObject
from ...utils import helper

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
    """The member's status in the chat. Can be 'creator', 'administrator', 'member', 'restricted',
    'left' or 'kicked'"""
    custom_title: Optional[str] = None
    """Owner and administrators only. Custom title for this user"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Restricted and kicked only. Date when restrictions will be lifted for this user; unix time"""
    can_be_edited: Optional[bool] = None
    """Administrators only. True, if the bot is allowed to edit administrator privileges of that
    user"""
    can_post_messages: Optional[bool] = None
    """Administrators only. True, if the administrator can post in the channel; channels only"""
    can_edit_messages: Optional[bool] = None
    """Administrators only. True, if the administrator can edit messages of other users and can
    pin messages; channels only"""
    can_delete_messages: Optional[bool] = None
    """Administrators only. True, if the administrator can delete messages of other users"""
    can_restrict_members: Optional[bool] = None
    """Administrators only. True, if the administrator can restrict, ban or unban chat members"""
    can_promote_members: Optional[bool] = None
    """Administrators only. True, if the administrator can add new administrators with a subset of
    their own privileges or demote administrators that he has promoted, directly or indirectly
    (promoted by administrators that were appointed by the user)"""
    can_change_info: Optional[bool] = None
    """Administrators and restricted only. True, if the user is allowed to change the chat title,
    photo and other settings"""
    can_invite_users: Optional[bool] = None
    """Administrators and restricted only. True, if the user is allowed to invite new users to the
    chat"""
    can_pin_messages: Optional[bool] = None
    """Administrators and restricted only. True, if the user is allowed to pin messages; groups
    and supergroups only"""
    is_member: Optional[bool] = None
    """Restricted only. True, if the user is a member of the chat at the moment of the request"""
    can_send_messages: Optional[bool] = None
    """Restricted only. True, if the user is allowed to send text messages, contacts, locations
    and venues"""
    can_send_media_messages: Optional[bool] = None
    """Restricted only. True, if the user is allowed to send audios, documents, photos, videos,
    video notes and voice notes"""
    can_send_polls: Optional[bool] = None
    """Restricted only. True, if the user is allowed to send polls"""
    can_send_other_messages: Optional[bool] = None
    """Restricted only. True, if the user is allowed to send animations, games, stickers and use
    inline bots"""
    can_add_web_page_previews: Optional[bool] = None
    """Restricted only. True, if the user is allowed to add web page previews to their messages"""

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
