from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class BanChatSenderChat(TelegramMethod[bool]):
    """
    Use this method to ban a channel chat in a supergroup or a channel. Until the chat is `unbanned <https://core.telegram.org/bots/api#unbanchatsenderchat>`_, the owner of the banned chat won't be able to send messages on behalf of **any of their channels**. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#banchatsenderchat
    """

    __returning__ = bool
    __api_method__ = "banChatSenderChat"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    sender_chat_id: int
    """Unique identifier of the target sender chat"""
