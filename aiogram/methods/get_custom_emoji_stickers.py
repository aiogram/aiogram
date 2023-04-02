from __future__ import annotations

from typing import TYPE_CHECKING, List

from ..types import Sticker
from .base import TelegramMethod


class GetCustomEmojiStickers(TelegramMethod[List[Sticker]]):
    """
    Use this method to get information about custom emoji stickers by their identifiers. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

    Source: https://core.telegram.org/bots/api#getcustomemojistickers
    """

    __returning__ = List[Sticker]
    __api_method__ = "getCustomEmojiStickers"

    custom_emoji_ids: List[str]
    """List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified."""
