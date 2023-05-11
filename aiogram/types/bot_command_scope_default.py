from __future__ import annotations

import msgspec

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeDefault(BotCommandScope, kw_only=True):
    """
    Represents the default `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands. Default commands are used if no commands with a `narrower scope <https://core.telegram.org/bots/api#determining-list-of-commands>`_ are specified for the user.

    Source: https://core.telegram.org/bots/api#botcommandscopedefault
    """

    type: str = msgspec.field(default_factory=lambda: BotCommandScopeType.DEFAULT)
    """Scope type, must be *default*"""
