from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject


class ForumTopic(TelegramObject):
    """
    This object represents a forum topic.

    Source: https://core.telegram.org/bots/api#forumtopic
    """

    message_thread_id: int
    """Unique identifier of the forum topic"""
    name: str
    """Name of the topic"""
    icon_color: int
    """Color of the topic icon in RGB format"""
    icon_custom_emoji_id: Optional[str] = None
    """*Optional*. Unique identifier of the custom emoji shown as the topic icon"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            message_thread_id: int,
            name: str,
            icon_color: int,
            icon_custom_emoji_id: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                message_thread_id=message_thread_id,
                name=name,
                icon_color=icon_color,
                icon_custom_emoji_id=icon_custom_emoji_id,
                **__pydantic_kwargs,
            )
