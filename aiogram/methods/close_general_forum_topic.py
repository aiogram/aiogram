from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class CloseGeneralForumTopic(TelegramMethod[bool]):
    """
    Use this method to close an open 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#closegeneralforumtopic
    """

    __returning__ = bool
    __api_method__ = "closeGeneralForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
