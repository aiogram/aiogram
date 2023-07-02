from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class UnbanChatSenderChat(TelegramMethod[bool]):
    """
    Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unbanchatsenderchat
    """

    __returning__ = bool
    __api_method__ = "unbanChatSenderChat"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    sender_chat_id: int
    """Unique identifier of the target sender chat"""
