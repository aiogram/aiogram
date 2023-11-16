from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ..enums import ChatMemberStatus
from .chat_member import ChatMember

if TYPE_CHECKING:
    from .user import User


class ChatMemberAdministrator(ChatMember):
    """
    Represents a `chat member <https://core.telegram.org/bots/api#chatmember>`_ that has some additional privileges.

    Source: https://core.telegram.org/bots/api#chatmemberadministrator
    """

    status: Literal[ChatMemberStatus.ADMINISTRATOR] = ChatMemberStatus.ADMINISTRATOR
    """The member's status in the chat, always 'administrator'"""
    user: User
    """Information about the user"""
    can_be_edited: bool
    """:code:`True`, if the bot is allowed to edit administrator privileges of that user"""
    is_anonymous: bool
    """:code:`True`, if the user's presence in the chat is hidden"""
    can_manage_chat: bool
    """:code:`True`, if the administrator can access the chat event log, boost list in channels, see channel members, report spam messages, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_delete_messages: bool
    """:code:`True`, if the administrator can delete messages of other users"""
    can_manage_video_chats: bool
    """:code:`True`, if the administrator can manage video chats"""
    can_restrict_members: bool
    """:code:`True`, if the administrator can restrict, ban or unban chat members, or access supergroup statistics"""
    can_promote_members: bool
    """:code:`True`, if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by the user)"""
    can_change_info: bool
    """:code:`True`, if the user is allowed to change the chat title, photo and other settings"""
    can_invite_users: bool
    """:code:`True`, if the user is allowed to invite new users to the chat"""
    can_post_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can post messages in the channel, or access channel statistics; channels only"""
    can_edit_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can edit messages of other users and can pin messages; channels only"""
    can_pin_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to pin messages; groups and supergroups only"""
    can_post_stories: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can post stories in the channel; channels only"""
    can_edit_stories: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can edit stories posted by other users; channels only"""
    can_delete_stories: Optional[bool] = None
    """*Optional*. :code:`True`, if the administrator can delete stories posted by other users; channels only"""
    can_manage_topics: Optional[bool] = None
    """*Optional*. :code:`True`, if the user is allowed to create, rename, close, and reopen forum topics; supergroups only"""
    custom_title: Optional[str] = None
    """*Optional*. Custom title for this user"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            status: Literal[ChatMemberStatus.ADMINISTRATOR] = ChatMemberStatus.ADMINISTRATOR,
            user: User,
            can_be_edited: bool,
            is_anonymous: bool,
            can_manage_chat: bool,
            can_delete_messages: bool,
            can_manage_video_chats: bool,
            can_restrict_members: bool,
            can_promote_members: bool,
            can_change_info: bool,
            can_invite_users: bool,
            can_post_messages: Optional[bool] = None,
            can_edit_messages: Optional[bool] = None,
            can_pin_messages: Optional[bool] = None,
            can_post_stories: Optional[bool] = None,
            can_edit_stories: Optional[bool] = None,
            can_delete_stories: Optional[bool] = None,
            can_manage_topics: Optional[bool] = None,
            custom_title: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                status=status,
                user=user,
                can_be_edited=can_be_edited,
                is_anonymous=is_anonymous,
                can_manage_chat=can_manage_chat,
                can_delete_messages=can_delete_messages,
                can_manage_video_chats=can_manage_video_chats,
                can_restrict_members=can_restrict_members,
                can_promote_members=can_promote_members,
                can_change_info=can_change_info,
                can_invite_users=can_invite_users,
                can_post_messages=can_post_messages,
                can_edit_messages=can_edit_messages,
                can_pin_messages=can_pin_messages,
                can_post_stories=can_post_stories,
                can_edit_stories=can_edit_stories,
                can_delete_stories=can_delete_stories,
                can_manage_topics=can_manage_topics,
                custom_title=custom_title,
                **__pydantic_kwargs,
            )
