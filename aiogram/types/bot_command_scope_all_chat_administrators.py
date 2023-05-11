from __future__ import annotations

import msgspec

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllChatAdministrators(BotCommandScope, kw_only=True):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chat administrators.

    Source: https://core.telegram.org/bots/api#botcommandscopeallchatadministrators
    """

    type: str = msgspec.field(default_factory=lambda: BotCommandScopeType.ALL_CHAT_ADMINISTRATORS)
    """Scope type, must be *all_chat_administrators*"""
