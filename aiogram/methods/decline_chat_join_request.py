from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class DeclineChatJoinRequest(TelegramMethod[bool]):
    """
    Use this method to decline a chat join request. The bot must be an administrator in the chat for this to work and must have the *can_invite_users* administrator right. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#declinechatjoinrequest
    """

    __returning__ = bool
    __api_method__ = "declineChatJoinRequest"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    user_id: int
    """Unique identifier of the target user"""
