from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from .background_type_chat_theme import BackgroundTypeChatTheme
    from .background_type_fill import BackgroundTypeFill
    from .background_type_pattern import BackgroundTypePattern
    from .background_type_wallpaper import BackgroundTypeWallpaper
from .base import TelegramObject


class ChatBackground(TelegramObject):
    """
    This object represents a chat background.

    Source: https://core.telegram.org/bots/api#chatbackground
    """

    type: Union[
        BackgroundTypeFill, BackgroundTypeWallpaper, BackgroundTypePattern, BackgroundTypeChatTheme
    ]
    """Type of the background"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Union[
                BackgroundTypeFill,
                BackgroundTypeWallpaper,
                BackgroundTypePattern,
                BackgroundTypeChatTheme,
            ],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, **__pydantic_kwargs)
