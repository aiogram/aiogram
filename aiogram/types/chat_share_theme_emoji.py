from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .chat_share_theme import ChatShareTheme

if TYPE_CHECKING:
    from .emoji_type_union import EmojiTypeUnion


class ChatShareThemeEmoji(ChatShareTheme):
    """
    The theme with emoji placed on a background.

    Source: https://core.telegram.org/bots/api#chatsharethemeemoji
    """

    type: Literal["emoji"] = "emoji"
    """Type of the theme, always 'emoji'"""
    emojis: list[EmojiTypeUnion]
    """The emoji; 0-6 regular or custom emoji"""
    background_backdrop_id: int | None = None
    """*Optional*. Identifier of the backdrop used as the background; omitted if the default background is used. Use :class:`aiogram.methods.get_chat_share_theme_backdrops.GetChatShareThemeBackdrops` to get details about the backdrop"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["emoji"] = "emoji",
            emojis: list[EmojiTypeUnion],
            background_backdrop_id: int | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                emojis=emojis,
                background_backdrop_id=background_backdrop_id,
                **__pydantic_kwargs,
            )
