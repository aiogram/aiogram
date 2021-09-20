from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .chat_member import ChatMember

if TYPE_CHECKING:
    from .user import User


class ChatMemberAdministrator(ChatMember):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that has some additional privileges.

    Source: https://core.telegram.org/bots/api#chatmemberadministrator
    """

    status: str = Field("administrator", const=True)
    """The member's status in the chat, always 'administrator'"""
    user: User
    """Information about the user"""
    can_be_edited: bool
    """True, if the bot is allowed to edit administrator privileges of that user"""
    is_anonymous: bool
    """True, if the user's presence in the chat is hidden"""
    can_manage_chat: bool
    """True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_delete_messages: bool
    """True, if the administrator can delete messages of other users"""
    can_manage_voice_chats: bool
    """True, if the administrator can manage voice chats"""
    can_restrict_members: bool
    """True, if the administrator can restrict, ban or unban chat members"""
    can_promote_members: bool
    """True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user)"""
    can_change_info: bool
    """True, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: bool
    """True, if the user is allowed to invite new users to the chat"""
    can_post_messages: Optional[bool] = None
    """*Optional*. True, if the administrator can post in the channel; channels only"""
    can_edit_messages: Optional[bool] = None
    """*Optional*. True, if the administrator can edit messages of other users and can pin messages; channels only"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. True, if the user is allowed to pin messages; groups and supergroups only"""
    custom_title: Optional[str] = None
    """*Optional*. Custom title for this user"""
