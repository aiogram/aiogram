from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .base import TelegramMethod


class PromoteChatMember(TelegramMethod[bool]):
    """
    Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#promotechatmember
    """

    __returning__ = bool
    __api_method__ = "promoteChatMember"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    is_anonymous: Optional[bool] = None
    """Pass :code:`True` if the administrator's presence in the chat is hidden"""
    can_manage_chat: Optional[bool] = None
    """Pass :code:`True` if the administrator can access the chat event log, get boost list, see hidden supergroup and channel members, report spam messages and ignore slow mode. Implied by any other administrator privilege."""
    can_delete_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can delete messages of other users"""
    can_manage_video_chats: Optional[bool] = None
    """Pass :code:`True` if the administrator can manage video chats"""
    can_restrict_members: Optional[bool] = None
    """Pass :code:`True` if the administrator can restrict, ban or unban chat members, or access supergroup statistics"""
    can_promote_members: Optional[bool] = None
    """Pass :code:`True` if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)"""
    can_change_info: Optional[bool] = None
    """Pass :code:`True` if the administrator can change chat title, photo and other settings"""
    can_invite_users: Optional[bool] = None
    """Pass :code:`True` if the administrator can invite new users to the chat"""
    can_post_stories: Optional[bool] = None
    """Pass :code:`True` if the administrator can post stories to the chat"""
    can_edit_stories: Optional[bool] = None
    """Pass :code:`True` if the administrator can edit stories posted by other users"""
    can_delete_stories: Optional[bool] = None
    """Pass :code:`True` if the administrator can delete stories posted by other users"""
    can_post_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can post messages in the channel, or access channel statistics; for channels only"""
    can_edit_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can edit messages of other users and can pin messages; for channels only"""
    can_pin_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can pin messages; for supergroups only"""
    can_manage_topics: Optional[bool] = None
    """Pass :code:`True` if the user is allowed to create, rename, close, and reopen forum topics; for supergroups only"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            user_id: int,
            is_anonymous: Optional[bool] = None,
            can_manage_chat: Optional[bool] = None,
            can_delete_messages: Optional[bool] = None,
            can_manage_video_chats: Optional[bool] = None,
            can_restrict_members: Optional[bool] = None,
            can_promote_members: Optional[bool] = None,
            can_change_info: Optional[bool] = None,
            can_invite_users: Optional[bool] = None,
            can_post_stories: Optional[bool] = None,
            can_edit_stories: Optional[bool] = None,
            can_delete_stories: Optional[bool] = None,
            can_post_messages: Optional[bool] = None,
            can_edit_messages: Optional[bool] = None,
            can_pin_messages: Optional[bool] = None,
            can_manage_topics: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                user_id=user_id,
                is_anonymous=is_anonymous,
                can_manage_chat=can_manage_chat,
                can_delete_messages=can_delete_messages,
                can_manage_video_chats=can_manage_video_chats,
                can_restrict_members=can_restrict_members,
                can_promote_members=can_promote_members,
                can_change_info=can_change_info,
                can_invite_users=can_invite_users,
                can_post_stories=can_post_stories,
                can_edit_stories=can_edit_stories,
                can_delete_stories=can_delete_stories,
                can_post_messages=can_post_messages,
                can_edit_messages=can_edit_messages,
                can_pin_messages=can_pin_messages,
                can_manage_topics=can_manage_topics,
                **__pydantic_kwargs,
            )
