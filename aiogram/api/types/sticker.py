from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .photo_size import PhotoSize
    from .mask_position import MaskPosition


class Sticker(TelegramObject):
    """
    This object represents a sticker.

    Source: https://core.telegram.org/bots/api#sticker
    """

    file_id: str
    """Identifier for this file"""
    width: int
    """Sticker width"""
    height: int
    """Sticker height"""
    is_animated: bool
    """True, if the sticker is animated"""
    thumb: Optional[PhotoSize] = None
    """Sticker thumbnail in the .webp or .jpg format"""
    emoji: Optional[str] = None
    """Emoji associated with the sticker"""
    set_name: Optional[str] = None
    """Name of the sticker set to which the sticker belongs"""
    mask_position: Optional[MaskPosition] = None
    """For mask stickers, the position where the mask should be placed"""
    file_size: Optional[int] = None
    """File size"""
