from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class BanChatSenderChat(TelegramMethod[bool]):
    """
    Use this method to ban a channel chat in a supergroup or a channel.
    The owner of the chat will not be able to send messages and join live streams on behalf of the chat,
    unless it is unbanned first. The bot must be an administrator in the supergroup or channel
    for this to work and must have the appropriate administrator rights. Returns True on success.

    Source: https://core.telegram.org/bots/api#banchatsenderchat
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername)`"""
    sender_chat_id: int
    """Unique identifier of the target sender chat"""
    until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Date when the sender chat will be unbanned, unix time. If the chat is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="banChatSenderChat", data=data)
