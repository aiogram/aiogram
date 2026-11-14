from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .chat_share_theme_backdrop import ChatShareThemeBackdrop


class ChatShareThemeBackdrops(TelegramObject):
    """
    This object contains a list of backdrops, which can be used as the background of a theme of the screen for sharing a link to a user or a chat.

    Source: https://core.telegram.org/bots/api#chatsharethemebackdrops
    """

    backdrops: list[ChatShareThemeBackdrop]
    """The list of backdrops"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            backdrops: list[ChatShareThemeBackdrop],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(backdrops=backdrops, **__pydantic_kwargs)
