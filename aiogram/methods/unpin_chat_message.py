from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramMethod


class UnpinChatMessage(TelegramMethod[bool]):
    """
    Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unpinchatmessage
    """

    __returning__ = bool
    __api_method__ = "unpinChatMessage"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: Optional[int] = None
    """Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned."""
