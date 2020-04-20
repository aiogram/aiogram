from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
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
    is_animated: bool
    """True, if the sticker set contains animated stickers"""
    contains_masks: bool
    """True, if the sticker set contains masks"""
    stickers: List[Sticker]
    """List of all set stickers"""
    thumb: Optional[PhotoSize] = None
    """Sticker set thumbnail in the .WEBP or .TGS format"""
