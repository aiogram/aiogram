from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class ForumTopicCreated(TelegramObject):
    """
    This object represents a service message about a new forum topic created in the chat.

    Source: https://core.telegram.org/bots/api#forumtopiccreated
    """

    name: str
    """Name of the topic"""
    icon_color: int
    """Color of the topic icon in RGB format"""
    icon_custom_emoji_id: Optional[str] = None
    """*Optional*. Unique identifier of the custom emoji shown as the topic icon"""
