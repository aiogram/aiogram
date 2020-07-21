from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .base import Request, TelegramMethod

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot


class UnpinChatMessage(TelegramMethod[bool]):
    """
    Use this method to unpin a message in a group, a supergroup, or a channel. The bot must be an
    administrator in the chat for this to work and must have the 'can_pin_messages' admin right in
    the supergroup or 'can_edit_messages' admin right in the channel. Returns True on success.

    Source: https://core.telegram.org/bots/api#unpinchatmessage
    """

    __returning__ = bool

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="unpinChatMessage", data=data)
