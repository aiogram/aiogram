from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import DeleteStickerFromSet, SetStickerPositionInSet
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

    def set_position_in_set(
        self,
        position: int,
        **kwargs: Any,
    ) -> SetStickerPositionInSet:
        """
        Shortcut for method :class:`aiogram.methods.set_sticker_position_in_set.SetStickerPositionInSet`
        will automatically fill method attributes:

        - :code:`sticker`

        Use this method to move a sticker in a set created by the bot to a specific position. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param position: New sticker position in the set, zero-based
        :return: instance of method :class:`aiogram.methods.set_sticker_position_in_set.SetStickerPositionInSet`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetStickerPositionInSet

        return SetStickerPositionInSet(
            sticker=self.file_id,
            position=position,
            **kwargs,
        )

    def delete_from_set(
        self,
        **kwargs: Any,
    ) -> DeleteStickerFromSet:
        """
        Shortcut for method :class:`aiogram.methods.delete_sticker_from_set.DeleteStickerFromSet`
        will automatically fill method attributes:

        - :code:`sticker`

        Use this method to delete a sticker from a set created by the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :return: instance of method :class:`aiogram.methods.delete_sticker_from_set.DeleteStickerFromSet`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeleteStickerFromSet

        return DeleteStickerFromSet(
            sticker=self.file_id,
            **kwargs,
        )
