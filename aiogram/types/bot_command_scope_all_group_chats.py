from __future__ import annotations

from typing import Literal

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllGroupChats(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallgroupchats
    """

    type: Literal[BotCommandScopeType.ALL_GROUP_CHATS] = BotCommandScopeType.ALL_GROUP_CHATS
    """Scope type, must be *all_group_chats*"""
