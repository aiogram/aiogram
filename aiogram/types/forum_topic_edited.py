from typing import Optional

from aiogram.types import TelegramObject


class ForumTopicEdited(TelegramObject):
    """
    This object represents a service message about an edited forum topic.

    Source: https://core.telegram.org/bots/api#forumtopicedited
    """

    name: Optional[str] = None
    """*Optional*. New name of the topic, if it was edited"""
    icon_custom_emoji_id: Optional[str] = None
    """*Optional*. New identifier of the custom emoji shown as the topic icon, if it was edited; an empty string if the icon was removed"""
