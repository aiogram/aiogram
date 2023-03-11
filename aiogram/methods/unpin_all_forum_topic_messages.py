from __future__ import annotations

from typing import TYPE_CHECKING, Union

from .base import TelegramMethod


class UnpinAllForumTopicMessages(TelegramMethod[bool]):
    """
    Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the chat for this to work and must have the *can_pin_messages* administrator right in the supergroup. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unpinallforumtopicmessages
    """

    __returning__ = bool
    __api_method__ = "unpinAllForumTopicMessages"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    message_thread_id: int
    """Unique identifier for the target message thread of the forum topic"""
