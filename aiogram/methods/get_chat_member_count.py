from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class GetChatMemberCount(TelegramMethod[int]):
    """
    Use this method to get the number of members in a chat. Returns *Int* on success.

    Source: https://core.telegram.org/bots/api#getchatmembercount
    """

    __returning__ = int
    __api_method__ = "getChatMemberCount"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
