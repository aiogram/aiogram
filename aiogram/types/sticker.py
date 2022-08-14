from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .file import File
    from .mask_position import MaskPosition
    from .photo_size import PhotoSize


class Sticker(TelegramObject):
    """
    This object represents a sticker.

    Source: https://core.telegram.org/bots/api#sticker
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    type: str
    """Type of the sticker, currently one of 'regular', 'mask', 'custom_emoji'. The type of the sticker is independent from its format, which is determined by the fields *is_animated* and *is_video*."""
    width: int
    """Sticker width"""
    height: int
    """Sticker height"""
    is_animated: bool
    """:code:`True`, if the sticker is `animated <https://telegram.org/blog/animated-stickers>`_"""
    is_video: bool
    """:code:`True`, if the sticker is a `video sticker <https://telegram.org/blog/video-stickers-better-reactions>`_"""
    thumb: Optional[PhotoSize] = None
    """*Optional*. Sticker thumbnail in the .WEBP or .JPG format"""
    emoji: Optional[str] = None
    """*Optional*. Emoji associated with the sticker"""
    set_name: Optional[str] = None
    """*Optional*. Name of the sticker set to which the sticker belongs"""
    premium_animation: Optional[File] = None
    """*Optional*. For premium regular stickers, premium animation for the sticker"""
    mask_position: Optional[MaskPosition] = None
    """*Optional*. For mask stickers, the position where the mask should be placed"""
    custom_emoji_id: Optional[str] = None
    """*Optional*. For custom emoji stickers, unique identifier of the custom emoji"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes"""
