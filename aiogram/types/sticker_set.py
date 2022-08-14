from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

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
    thumb: Optional[PhotoSize] = None
    """*Optional*. Sticker set thumbnail in the .WEBP, .TGS, or .WEBM format"""
