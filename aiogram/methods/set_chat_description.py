from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramMethod


class SetChatDescription(TelegramMethod[bool]):
    """
    Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatdescription
    """

    __returning__ = bool
    __api_method__ = "setChatDescription"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    description: Optional[str] = None
    """New chat description, 0-255 characters"""
