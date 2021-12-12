from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class BanChatSenderChat(TelegramMethod[bool]):
    """
    Use this method to ban a channel chat in a supergroup or a channel. Until the chat is `unbanned <https://core.telegram.org/bots/api#unbanchatsenderchat>`_, the owner of the banned chat won't be able to send messages on behalf of **any of their channels**. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#banchatsenderchat
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    sender_chat_id: int
    """Unique identifier of the target sender chat"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="banChatSenderChat", data=data)
