from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import InputFile, InputSticker
from .base import Request, TelegramMethod, prepare_input_sticker

if TYPE_CHECKING:
    from ..client.bot import Bot


class AddStickerToSet(TelegramMethod[bool]):
    """
    Use this method to add a new sticker to a set created by the bot. The format of the added sticker must match the format of the other stickers in the set. Emoji sticker sets can have up to 200 stickers. Animated and video sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#addstickertoset
    """

    __returning__ = bool

    user_id: int
    """User identifier of sticker set owner"""
    name: str
    """Sticker set name"""
    sticker: InputSticker
    """A JSON-serialized object with information about the added sticker. If exactly the same sticker had already been added to the set, then the set isn't changed."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        files: Dict[str, InputFile] = {}
        prepare_input_sticker(input_sticker=data["sticker"], files=files)

        return Request(method="addStickerToSet", data=data, files=files)
