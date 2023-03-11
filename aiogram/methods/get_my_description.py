from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..types import BotDescription
from .base import TelegramMethod


class GetMyDescription(TelegramMethod[BotDescription]):
    """
    Use this method to get the current bot description for the given user language. Returns :class:`aiogram.types.bot_description.BotDescription` on success.

    Source: https://core.telegram.org/bots/api#getmydescription
    """

    __returning__ = BotDescription
    __api_method__ = "getMyDescription"

    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code or an empty string"""
