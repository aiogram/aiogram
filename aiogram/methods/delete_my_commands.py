from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from ..types import BotCommandScope
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class DeleteMyCommands(TelegramMethod[bool]):
    """
    Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, `higher level commands <https://core.telegram.org/bots/api#determining-list-of-commands>`_ will be shown to affected users. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deletemycommands
    """

    __returning__ = bool

    scope: Optional[BotCommandScope] = None
    """A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="deleteMyCommands", data=data)
