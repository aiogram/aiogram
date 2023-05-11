from __future__ import annotations

import msgspec

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllPrivateChats(BotCommandScope, kw_only=True):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all private chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallprivatechats
    """

    type: str = msgspec.field(default_factory=lambda: BotCommandScopeType.ALL_PRIVATE_CHATS)
    """Scope type, must be *all_private_chats*"""
