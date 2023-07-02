from __future__ import annotations

from typing import Optional

from .base import TelegramMethod


class SetCustomEmojiStickerSetThumbnail(TelegramMethod[bool]):
    """
    Use this method to set the thumbnail of a custom emoji sticker set. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setcustomemojistickersetthumbnail
    """

    __returning__ = bool
    __api_method__ = "setCustomEmojiStickerSetThumbnail"

    name: str
    """Sticker set name"""
    custom_emoji_id: Optional[str] = None
    """Custom emoji identifier of a sticker from the sticker set; pass an empty string to drop the thumbnail and use the first sticker as the thumbnail."""
