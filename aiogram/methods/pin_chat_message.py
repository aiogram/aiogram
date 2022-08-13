from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class PinChatMessage(TelegramMethod[bool]):
    """
    Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#pinchatmessage
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: int
    """Identifier of a message to pin"""
    disable_notification: Optional[bool] = None
    """Pass :code:`True` if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="pinChatMessage", data=data)
