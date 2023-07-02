from __future__ import annotations

from typing import Union

from ..types import Chat
from .base import TelegramMethod


class GetChat(TelegramMethod[Chat]):
    """
    Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a :class:`aiogram.types.chat.Chat` object on success.

    Source: https://core.telegram.org/bots/api#getchat
    """

    __returning__ = Chat
    __api_method__ = "getChat"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
