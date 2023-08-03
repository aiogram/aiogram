from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize
    from .sticker import Sticker


class StickerSet(TelegramObject):
    """
    This object represents a sticker set.

    Source: https://core.telegram.org/bots/api#stickerset
    """

    name: str
    """Sticker set name"""
    title: str
    """Sticker set title"""
    sticker_type: str
    """Type of stickers in the set, currently one of 'regular', 'mask', 'custom_emoji'"""
    is_animated: bool
    """:code:`True`, if the sticker set contains `animated stickers <https://telegram.org/blog/animated-stickers>`_"""
    is_video: bool
    """:code:`True`, if the sticker set contains `video stickers <https://telegram.org/blog/video-stickers-better-reactions>`_"""
    stickers: List[Sticker]
    """List of all set stickers"""
    thumbnail: Optional[PhotoSize] = None
    """*Optional*. Sticker set thumbnail in the .WEBP, .TGS, or .WEBM format"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            name: str,
            title: str,
            sticker_type: str,
            is_animated: bool,
            is_video: bool,
            stickers: List[Sticker],
            thumbnail: Optional[PhotoSize] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                name=name,
                title=title,
                sticker_type=sticker_type,
                is_animated=is_animated,
                is_video=is_video,
                stickers=stickers,
                thumbnail=thumbnail,
                **__pydantic_kwargs,
            )
