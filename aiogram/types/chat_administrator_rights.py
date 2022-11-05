from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    pass


class ChatAdministratorRights(TelegramObject):
    """
    Represents the rights of an administrator in a chat.

    Source: https://core.telegram.org/bots/api#chatadministratorrights
    """

    is_anonymous: bool
    """:code:`True`, if the user's presence in the chat is hidden"""
    can_manage_chat: bool
    """:code:`True`, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_delete_messages: bool
    """:code:`True`, if the administrator can delete messages of other users"""
    can_manage_video_chats: bool
    """:code:`True`, if the administrator can manage video chats"""
    can_restrict_members: bool
    """:code:`True`, if the administrator can restrict, ban or unban chat members"""
    can_promote_members: bool
    """:code:`True`, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user)"""
    can_change_info: bool
    """:code:`True`, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: bool
    """:code:`True`, if the user is allowed to invite new users to the chat"""
    can_post_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can post in the channel; channels only"""
    can_edit_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can edit messages of other users and can pin messages; channels only"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to pin messages; groups and supergroups only"""
    can_manage_topics: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to create, rename, close, and reopen forum topics; supergroups only"""
