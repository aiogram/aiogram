from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class SetChatTitle(TelegramMethod[bool]):
    """
    Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchattitle
    """

    __returning__ = bool
    __api_method__ = "setChatTitle"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    title: str
    """New chat title, 1-128 characters"""
