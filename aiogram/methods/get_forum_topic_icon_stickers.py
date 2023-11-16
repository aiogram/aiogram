from __future__ import annotations

from typing import List

from ..types import Sticker
from .base import TelegramMethod


class GetForumTopicIconStickers(TelegramMethod[List[Sticker]]):
    """
    Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

    Source: https://core.telegram.org/bots/api#getforumtopiciconstickers
    """

    __returning__ = List[Sticker]
    __api_method__ = "getForumTopicIconStickers"
