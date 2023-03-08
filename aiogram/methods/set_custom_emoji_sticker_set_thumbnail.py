from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetCustomEmojiStickerSetThumbnail(TelegramMethod[bool]):
    """
    Use this method to set the thumbnail of a custom emoji sticker set. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setcustomemojistickersetthumbnail
    """

    __returning__ = bool

    name: str
    """Sticker set name"""
    custom_emoji_id: Optional[str] = None
    """Custom emoji identifier of a sticker from the sticker set; pass an empty string to drop the thumbnail and use the first sticker as the thumbnail."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setCustomEmojiStickerSetThumbnail", data=data)
