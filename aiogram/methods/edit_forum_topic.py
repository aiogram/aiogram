from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from .base import TelegramMethod


class EditForumTopic(TelegramMethod[bool]):
    """
    Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an administrator in the chat for this to work and must have *can_manage_topics* administrator rights, unless it is the creator of the topic. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#editforumtopic
    """

    __returning__ = bool
    __api_method__ = "editForumTopic"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    message_thread_id: int
    """Unique identifier for the target message thread of the forum topic"""
    name: Optional[str] = None
    """New topic name, 0-128 characters. If not specified or empty, the current name of the topic will be kept"""
    icon_custom_emoji_id: Optional[str] = None
    """New unique identifier of the custom emoji shown as the topic icon. Use :class:`aiogram.methods.get_forum_topic_icon_stickers.GetForumTopicIconStickers` to get all allowed custom emoji identifiers. Pass an empty string to remove the icon. If not specified, the current icon will be kept"""
