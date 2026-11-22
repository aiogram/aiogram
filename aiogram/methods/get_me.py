from __future__ import annotations

from ..types import BotFullInfo, User
from .base import TelegramMethod


class GetMe(TelegramMethod[BotFullInfo]):
    """
    A simple method for testing your bot's authentication token. Requires no parameters. Returns information about the bot in form of a :class:`aiogram.types.bot_full_info.BotFullInfo` object.

    Source: https://core.telegram.org/bots/api#getme
    """

    __returning__ = BotFullInfo
    __api_method__ = "getMe"
