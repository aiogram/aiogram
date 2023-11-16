from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

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

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            name: str,
            icon_color: int,
            icon_custom_emoji_id: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                name=name,
                icon_color=icon_color,
                icon_custom_emoji_id=icon_custom_emoji_id,
                **__pydantic_kwargs,
            )
