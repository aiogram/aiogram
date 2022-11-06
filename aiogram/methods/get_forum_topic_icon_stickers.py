from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ..types import Sticker
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetForumTopicIconStickers(TelegramMethod[List[Sticker]]):
    """
    Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user. Requires no parameters. Returns an Array of :class:`aiogram.types.sticker.Sticker` objects.

    Source: https://core.telegram.org/bots/api#getforumtopiciconstickers
    """

    __returning__ = List[Sticker]

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getForumTopicIconStickers", data=data)
