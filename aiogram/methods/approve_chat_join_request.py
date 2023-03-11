from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class ApproveChatJoinRequest(TelegramMethod[bool]):
    """
    Use this method to approve a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#approvechatjoinrequest
    """

    __returning__ = bool
    __api_method__ = "approveChatJoinRequest"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
