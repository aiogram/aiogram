from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class LeaveChat(TelegramMethod[bool]):
    """
    Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#leavechat
    """

    __returning__ = bool
    __api_method__ = "leaveChat"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""
