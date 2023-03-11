from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class CloseForumTopic(TelegramMethod[bool]):
    """
    Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#closeforumtopic
    """

    __returning__ = bool
    __api_method__ = "closeForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    message_thread_id: int
    """Unique identifier for the target message thread of the forum topic"""
