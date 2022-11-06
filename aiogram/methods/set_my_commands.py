from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types import BotCommand, BotCommandScope
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetMyCommands(TelegramMethod[bool]):
    """
    Use this method to change the list of the bot's commands. See `this manual <https://core.telegram.org/bots/features#commands>`_ for more details about bot commands. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmycommands
    """

    __returning__ = bool

    commands: List[BotCommand]
    """A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified."""
    scope: Optional[BotCommandScope] = None
    """A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setMyCommands", data=data)
