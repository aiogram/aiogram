from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ..types import Sticker
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetCustomEmojiStickers(TelegramMethod[List[Sticker]]):
    """
    Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

    Source: https://core.telegram.org/bots/api#getcustomemojistickers
    """

    __returning__ = List[Sticker]

    custom_emoji_ids: List[str]
    """List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getCustomEmojiStickers", data=data)
