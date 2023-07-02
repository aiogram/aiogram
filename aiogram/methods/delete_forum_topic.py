from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class DeleteForumTopic(TelegramMethod[bool]):
    """
    Use this method to delete a forum topic along with all its messages in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have the *can_delete_messages* administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deleteforumtopic
    """

    __returning__ = bool
    __api_method__ = "deleteForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    message_thread_id: int
    """Unique identifier for the target message thread of the forum topic"""
