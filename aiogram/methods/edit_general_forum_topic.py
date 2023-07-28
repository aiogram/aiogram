from __future__ import annotations

from typing import Union

from .base import TelegramMethod


class EditGeneralForumTopic(TelegramMethod[bool]):
    """
    Use this method to edit the name of the 'General' topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#editgeneralforumtopic
    """

    __returning__ = bool
    __api_method__ = "editGeneralForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    name: str
    """New topic name, 1-128 characters"""
