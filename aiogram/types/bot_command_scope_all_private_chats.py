from __future__ import annotations

from pydantic import Field

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllPrivateChats(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all private chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallprivatechats
    """

    type: str = Field(BotCommandScopeType.ALL_PRIVATE_CHATS, const=True)
    """Scope type, must be *all_private_chats*"""
