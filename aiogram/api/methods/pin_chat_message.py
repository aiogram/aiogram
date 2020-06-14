from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class PinChatMessage(TelegramMethod[bool]):
    """
    Use this method to pin a message in a group, a supergroup, or a channel. The bot must be an
    administrator in the chat for this to work and must have the 'can_pin_messages' admin right in
    the supergroup or 'can_edit_messages' admin right in the channel. Returns True on success.

    Source: https://core.telegram.org/bots/api#pinchatmessage
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    message_id: int
    """Identifier of a message to pin"""
    disable_notification: Optional[bool] = None
    """Pass True, if it is not necessary to send a notification to all chat members about the new
    pinned message. Notifications are always disabled in channels."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="pinChatMessage", data=data)
