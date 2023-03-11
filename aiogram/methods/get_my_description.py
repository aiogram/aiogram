from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from ..types import BotDescription
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetMyDescription(TelegramMethod[BotDescription]):
    """
    Use this method to get the current bot description for the given user language. Returns :class:`aiogram.types.bot_description.BotDescription` on success.

    Source: https://core.telegram.org/bots/api#getmydescription
    """

    __returning__ = BotDescription

    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code or an empty string"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMyDescription", data=data)
