from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .unique_gift_backdrop_colors import UniqueGiftBackdropColors


class ChatShareThemeBackdrop(TelegramObject):
    """
    This object describes a backdrop, which can be used as the background of a theme of the screen for sharing a link to a user or a chat.

    Source: https://core.telegram.org/bots/api#chatsharethemebackdrop
    """

    id: int
    """Unique identifier of the backdrop"""
    name: str
    """Name of the backdrop"""
    colors: UniqueGiftBackdropColors
    """Colors of the backdrop"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: int,
            name: str,
            colors: UniqueGiftBackdropColors,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(id=id, name=name, colors=colors, **__pydantic_kwargs)
