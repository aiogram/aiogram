from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class PromoteChatMember(TelegramMethod[bool]):
    """
    Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#promotechatmember
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
    is_anonymous: Optional[bool] = None
    """Pass :code:`True` if the administrator's presence in the chat is hidden"""
    can_manage_chat: Optional[bool] = None
    """Pass :code:`True` if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege"""
    can_post_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can create channel posts, channels only"""
    can_edit_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can edit messages of other users and can pin messages, channels only"""
    can_delete_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can delete messages of other users"""
    can_manage_video_chats: Optional[bool] = None
    """Pass :code:`True` if the administrator can manage video chats"""
    can_restrict_members: Optional[bool] = None
    """Pass :code:`True` if the administrator can restrict, ban or unban chat members"""
    can_promote_members: Optional[bool] = None
    """Pass :code:`True` if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by him)"""
    can_change_info: Optional[bool] = None
    """Pass :code:`True` if the administrator can change chat title, photo and other settings"""
    can_invite_users: Optional[bool] = None
    """Pass :code:`True` if the administrator can invite new users to the chat"""
    can_pin_messages: Optional[bool] = None
    """Pass :code:`True` if the administrator can pin messages, supergroups only"""
    can_manage_topics: Optional[bool] = None
    """Pass :code:`True` if the user is allowed to create, rename, close, and reopen forum topics, supergroups only"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="promoteChatMember", data=data)
