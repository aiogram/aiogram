from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .chat_share_theme import ChatShareTheme

if TYPE_CHECKING:
    from .unique_gift import UniqueGift


class ChatShareThemeUniqueGift(ChatShareTheme):
    """
    The theme based on a unique gift owned by the user or the chat.

    Source: https://core.telegram.org/bots/api#chatsharethemeuniquegift
    """

    type: Literal["unique_gift"] = "unique_gift"
    """Type of the theme, always 'unique_gift'"""
    gift: UniqueGift
    """The gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["unique_gift"] = "unique_gift",
            gift: UniqueGift,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, gift=gift, **__pydantic_kwargs)
