from __future__ import annotations

from pydantic import Field

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllGroupChats(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallgroupchats
    """

    type: str = Field(BotCommandScopeType.ALL_GROUP_CHATS, const=True)
    """Scope type, must be *all_group_chats*"""
