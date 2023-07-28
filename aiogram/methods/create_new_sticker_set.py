from __future__ import annotations

from typing import List, Optional

from ..types import InputSticker
from .base import TelegramMethod


class CreateNewStickerSet(TelegramMethod[bool]):
    """
    Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#createnewstickerset
    """

    __returning__ = bool
    __api_method__ = "createNewStickerSet"

    user_id: int
    """User identifier of created sticker set owner"""
    name: str
    """Short name of sticker set, to be used in :code:`t.me/addstickers/` URLs (e.g., *animals*). Can contain only English letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in :code:`"_by_<bot_username>"`. :code:`<bot_username>` is case insensitive. 1-64 characters."""
    title: str
    """Sticker set title, 1-64 characters"""
    stickers: List[InputSticker]
    """A JSON-serialized list of 1-50 initial stickers to be added to the sticker set"""
    sticker_format: str
    """Format of stickers in the set, must be one of 'static', 'animated', 'video'"""
    sticker_type: Optional[str] = None
    """Type of stickers in the set, pass 'regular', 'mask', or 'custom_emoji'. By default, a regular sticker set is created."""
    needs_repainting: Optional[bool] = None
    """Pass :code:`True` if stickers in the sticker set must be repainted to the color of text when used in messages, the accent color if used as emoji status, white on chat photos, or another appropriate color based on context; for custom emoji sticker sets only"""
