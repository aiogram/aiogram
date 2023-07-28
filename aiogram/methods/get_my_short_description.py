from __future__ import annotations

from typing import Optional

from ..types import BotShortDescription
from .base import TelegramMethod


class GetMyShortDescription(TelegramMethod[BotShortDescription]):
    """
    Use this method to get the current bot short description for the given user language. Returns :class:`aiogram.types.bot_short_description.BotShortDescription` on success.

    Source: https://core.telegram.org/bots/api#getmyshortdescription
    """

    __returning__ = BotShortDescription
    __api_method__ = "getMyShortDescription"

    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code or an empty string"""
