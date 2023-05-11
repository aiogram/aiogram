from __future__ import annotations

import msgspec

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllGroupChats(BotCommandScope, kw_only=True):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallgroupchats
    """

    type: str = msgspec.field(default_factory=lambda: BotCommandScopeType.ALL_GROUP_CHATS)
    """Scope type, must be *all_group_chats*"""
