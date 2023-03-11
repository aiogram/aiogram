from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class ReopenGeneralForumTopic(TelegramMethod[bool]):
    """
    Use this method to reopen a closed 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights. The topic will be automatically unhidden if it was hidden. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#reopengeneralforumtopic
    """

    __returning__ = bool
    __api_method__ = "reopenGeneralForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
