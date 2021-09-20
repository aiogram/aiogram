from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import BotCommand, BotCommandScope
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetMyCommands(TelegramMethod[List[BotCommand]]):
    """
    Use this method to get the current list of the bot's commands for the given scope and user language. Returns Array of :class:`aiogram.types.bot_command.BotCommand` on success. If commands aren't set, an empty list is returned.

    Source: https://core.telegram.org/bots/api#getmycommands
    """

    __returning__ = List[BotCommand]

    scope: Optional[BotCommandScope] = None
    """A JSON-serialized object, describing scope of users. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code or an empty string"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getMyCommands", data=data)
